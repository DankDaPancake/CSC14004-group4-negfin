"""Frozen SPMF/Julia Optimized cold campaigns; raw evidence stays outside Git."""
import argparse
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tomllib
import uuid


def _sibling(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


process_tools = _sibling('spmf_process')
validator = _sibling('spmf_validate')
RUN_COLUMNS = ['schema_version', 'fingerprint', 'attempt_id', 'scope', 'dataset',
               'minsup', 'min_count', 'input_sha256', 'n_transactions', 'repetition',
               'variant', 'status', 'exit_code', 'process_wall_seconds', 'maxrss_bytes',
               'output_bytes', 'started_at', 'finished_at', 'rss_method']


def _json(path, value):
    """Atomic replacement of our own evidence file, never a foreign file."""
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with temporary.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _hash(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def expected_min_count(minsup: str, n_transactions: int) -> int:
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', minsup) or n_transactions < 0:
        raise ValueError('Invalid decimal minsup/transaction count')
    ratio = Fraction(minsup)
    if not 0 < ratio <= 1:
        raise ValueError('minsup outside (0,1]')
    return math.ceil(ratio * n_transactions)


def threshold_info(minsup, n_transactions):
    exact = expected_min_count(minsup, n_transactions)
    binary = math.ceil(float(minsup) * n_transactions)
    return dict(exact=exact, binary_ceil=binary, matches=exact == binary)


def spmf_ratio(minsup, n_transactions):
    """Documented binary-CLI encoding of the requested exact absolute threshold.

    SPMF 2.69 source scanDB uses ceil(double*N). Move at most 16 adjacent
    doubles and verify the resulting ceiling; never change the exact target.
    Actual argv/mapping is saved in each measurement, including unchanged cases.
    """
    target = expected_min_count(minsup, n_transactions)
    value = float(minsup)
    effective = minsup
    for _ in range(17):
        observed = math.ceil(value * n_transactions)
        if observed == target:
            return dict(requested=minsup, effective=effective, min_count=target,
                        policy='exact-ceil-cli-v1', adjusted=effective != minsup)
        value = math.nextafter(value, -math.inf if observed > target else math.inf)
        effective = repr(value)
    raise ValueError('Cannot encode exact threshold for SPMF CLI')


def load_campaign(config: Path, repo: Path) -> dict:
    with Path(config).open('rb') as handle:
        result = tomllib.load(handle)
    with (repo / result['reference_config']).open('rb') as handle:
        reference = tomllib.load(handle)
    if result['selected'] != reference['selected'] or len(result['selected']) != 5:
        raise ValueError('selected levels differ from frozen baseline config')
    if result['schema_version'] != 1 or result['cold_repetitions'] != 3:
        raise ValueError('Unsupported schema/repetition count')
    for key in ('timeout_seconds', 'output_cap_bytes', 'rss_cap_bytes', 'poll_seconds',
                'minimum_free_disk_bytes', 'validation_chunk_bytes',
                'validation_fan_in', 'validation_scratch_cap_bytes'):
        if not isinstance(result[key], (int, float)) or result[key] <= 0:
            raise ValueError(f'Invalid limit {key}')
    if result['validation_fan_in'] < 2:
        raise ValueError('Invalid validation fan-in')
    for levels in result['selected'].values():
        if len(levels) != 7 or len(set(levels)) != 7:
            raise ValueError('Need seven unique selected levels')
        for level in levels:
            expected_min_count(level, 1)
    return result


def inspect_input(path, *, expected_sha256=None, expected_transactions=None):
    digest = _hash(path)
    if expected_sha256 is not None and digest != expected_sha256.lower():
        raise ValueError(f'Checksum mismatch: {path}')
    count = 0
    with Path(path).open(encoding='utf-8-sig') as handle:
        for line in handle:
            text = line.strip()
            if not text or text[0] in '#%@':
                continue
            items = text.split()
            if any(not re.fullmatch(r'[0-9]+', x) or int(x) <= 0 for x in items):
                raise ValueError(f'Invalid input record: {path}')
            count += 1
    if expected_transactions is not None and count != expected_transactions:
        raise ValueError(f'Unexpected transactions: {path}: {count}')
    return dict(sha256=digest, n_transactions=count)


def build_command(variant: str, *, julia: Path, java: Path, jar: Path, repo: Path,
                  input_path: Path, output_path: Path, minsup: str, stats_path: Path) -> list[str]:
    if variant == 'spmf':
        return [str(java), '-XX:ActiveProcessorCount=1', '-Xmx4g', '-jar', str(jar),
                'run', 'NegFIN', str(input_path), str(output_path), minsup]
    if variant == 'optimized':
        return [str(julia), '--startup-file=no', '--threads=1', f'--project={repo}',
                str(repo / 'run.jl'), '--input', str(input_path), '--output', str(output_path),
                '--minsup', minsup, '--variant', 'optimized', '--stats', str(stats_path)]
    raise ValueError(f'Unsupported variant: {variant}')


def schedule(config: dict) -> list[dict]:
    return [dict(dataset=dataset, minsup=minsup, repetition=repetition, variant=variant)
            for dataset, levels in config['selected'].items() for minsup in levels
            for repetition in range(1, 4)
            for variant in (('spmf', 'optimized') if repetition % 2 else ('optimized', 'spmf'))]


def _command_output(argv):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=30,
                            stdin=subprocess.DEVNULL)
    if result.returncode:
        raise ValueError(f'Command failed: {argv}: {result.stderr}')
    return (result.stdout + result.stderr).strip()


def runtime_info(julia, java, jar):
    for path in (julia, java, jar):
        if not Path(path).is_file():
            raise ValueError(f'Missing runtime/jar: {path}')
    julia_version = _command_output([str(julia), '--startup-file=no', '--version'])
    java_version = _command_output([str(java), '--version'])
    spmf_version = _command_output([str(java), '-jar', str(jar), 'version'])
    if not re.search(r'julia version \d', julia_version) or not re.search(r'\d', java_version) \
            or not re.search(r'SPMF version\s+\S+', spmf_version):
        raise ValueError('Cannot verify runtime versions')
    return dict(julia=str(Path(julia).resolve()), java=str(Path(java).resolve()),
                jar=str(Path(jar).resolve()), julia_version=julia_version,
                java_version=java_version, spmf_version=spmf_version,
                julia_sha256=_hash(julia), java_sha256=_hash(java), jar_sha256=_hash(jar))


def append_measurement(path, row):
    fresh = not path.exists()
    with path.open('a', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=RUN_COLUMNS, extrasaction='ignore')
        if fresh:
            writer.writeheader()
        writer.writerow(row)
        handle.flush()
        os.fsync(handle.fileno())


def read_measurements(path):
    if not path.exists():
        return []
    data = path.read_bytes()
    if not data.endswith(b'\n'):
        raise ValueError('CSV has partial tail; preserve evidence and repair explicitly')
    with path.open(encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle, strict=True)
        if reader.fieldnames != RUN_COLUMNS:
            raise ValueError('CSV schema mismatch')
        rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError('CSV malformed row')
    if len({row['attempt_id'] for row in rows}) != len(rows):
        raise ValueError('CSV duplicate attempt')
    return rows


def completed_slots(rows, fingerprint):
    keys = set()
    for row in rows:
        if row['fingerprint'] != fingerprint:
            raise ValueError('Mixed provenance in CSV')
        if row['scope'] != 'main':
            continue
        key = (row['dataset'], row['minsup'], int(row['repetition']), row['variant'])
        if key in keys:
            raise ValueError('CSV duplicate main slot')
        keys.add(key)
    return keys


def check_resume(root, current):
    old = json.loads((root / 'campaign.json').read_text(encoding='utf-8'))
    if old['fingerprint'] != current['fingerprint']:
        raise ValueError('Changed campaign provenance; create a new campaign')
    read_measurements(root / 'runs.csv')
    return old


def require_pilot(root, fingerprint):
    path = root / 'pilot.json'
    if not path.exists():
        raise ValueError('Verified pilot required before main')
    pilot = json.loads(path.read_text(encoding='utf-8'))
    results = pilot.get('results', [])
    if (pilot.get('fingerprint') != fingerprint or not pilot.get('ok')
            or len(results) != 9 or not all(r.get('equal') for r in results)
            or any(r.get('fingerprint') != fingerprint for r in results)):
        raise ValueError('Verified matching pilot required before main')
    for name in fixture_expectations():
        matching = [r for r in results if r.get('dataset') == name]
        if len(matching) != 1 or not fixture_matches(name, matching[0]):
            raise ValueError('Hand-checked fixture pilot evidence missing')
    return pilot


def preflight(config_path, repo, julia, java, jar):
    config = load_campaign(config_path, repo)
    runtimes = runtime_info(julia, java, jar)
    with (repo / config['manifest']).open('rb') as handle:
        manifest = tomllib.load(handle)
    datasets = {}
    for entry in manifest['datasets']:
        path = (repo / config['manifest']).parent / entry['path']
        info = inspect_input(path, expected_sha256=entry['sha256'],
                             expected_transactions=entry['expected_transactions'])
        datasets[entry['name']] = dict(input_path=str(path.resolve()),
            input_sha256=info['sha256'], n_transactions=info['n_transactions'],
            thresholds={m: threshold_info(m, info['n_transactions'])
                        for m in config['selected'][entry['name']]})
    source_paths = [repo / 'run.jl', repo / 'Project.toml', config_path,
                    repo / config['manifest'], repo / config['reference_config']]
    source_paths += sorted((repo / 'src').glob('*.jl'))
    source_paths += sorted((repo / 'bench').glob('spmf_*.py'))
    sources = {str(p.resolve()): _hash(p) for p in source_paths}
    # Capture stable machine characteristics; do not fingerprint current free RAM.
    host = dict(platform=platform.platform(), machine=platform.machine(),
                processor=platform.processor(), logical_cpus=os.cpu_count(),
                python=sys.version, julia_threads=1, java_active_processors=1,
                java_max_heap_bytes=4 * 1024 ** 3,
                thread_env={k: os.environ.get(k, '') for k in
                            ('JULIA_NUM_THREADS', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS')})
    if os.name == 'nt':
        details = _command_output(['powershell.exe', '-NoProfile', '-NonInteractive',
            '-Command', "[pscustomobject]@{CPU=(Get-CimInstance Win32_Processor).Name;RAM=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory;OS=(Get-CimInstance Win32_OperatingSystem).Caption;Build=(Get-CimInstance Win32_OperatingSystem).BuildNumber}|ConvertTo-Json -Compress"])
        host['windows'] = json.loads(details)
    meta = dict(schema_version=1, config=config, repo=str(repo), runtimes=runtimes,
                datasets=datasets, sources=sources, host=host,
                git_commit=_command_output(['git', '-C', str(repo), 'rev-parse', 'HEAD']),
                git_status=_command_output(['git', '-C', str(repo), 'status', '--porcelain']),
                git_diff=_command_output(['git', '-C', str(repo), 'diff', '--binary', 'HEAD']))
    meta['fingerprint'] = hashlib.sha256(json.dumps(meta, sort_keys=True).encode()).hexdigest()
    meta['created_at'] = datetime.now(timezone.utc).isoformat()
    return meta


def _condition_id(scope, case):
    text = json.dumps([scope, case['dataset'], case['minsup']], separators=(',', ':'))
    return hashlib.sha256(text.encode()).hexdigest()[:20]


def run_condition(root, meta, case, *, scope, repetitions):
    """Append attempts, validate exact first pair, retain explicit failures on resume."""
    root = Path(root)
    verify_sources(meta)
    config = meta['config']
    condition_id = _condition_id(scope, case)
    evidence_dir = root / 'conditions' / condition_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    summary_path = evidence_dir / 'condition.json'
    if summary_path.exists():
        saved = json.loads(summary_path.read_text(encoding='utf-8'))
        if saved['fingerprint'] != meta['fingerprint']:
            raise ValueError('Condition provenance mismatch')
        return saved
    rows = read_measurements(root / 'runs.csv')
    completed_slots(rows, meta['fingerprint'])
    selected = [r for r in rows if r['scope'] == scope and r['dataset'] == case['dataset']
                and r['minsup'] == case['minsup']]
    slot_rows = {(int(r['repetition']), r['variant']): r for r in selected}
    if len(slot_rows) != len(selected):
        raise ValueError('Duplicate condition slot')
    base = dict(schema_version=1, fingerprint=meta['fingerprint'], scope=scope,
                dataset=case['dataset'], minsup=case['minsup'],
                min_count=expected_min_count(case['minsup'], case['n_transactions']),
                input_sha256=case['input_sha256'], n_transactions=case['n_transactions'])
    validations = {}
    comparison = None
    for repetition in range(1, repetitions + 1):
        order = ('spmf', 'optimized') if repetition % 2 else ('optimized', 'spmf')
        for variant in order:
            row = slot_rows.get((repetition, variant))
            if row is None:
                process_tools.require_disk(root, config['minimum_free_disk_bytes'])
                attempt_id = uuid.uuid4().hex
                directory = root / 'attempts' / attempt_id
                mapping = spmf_ratio(case['minsup'], case['n_transactions'])
                effective_minsup = mapping['effective'] if variant == 'spmf' else case['minsup']
                argv = build_command(variant, julia=Path(meta['runtimes']['julia']),
                    java=Path(meta['runtimes']['java']), jar=Path(meta['runtimes']['jar']),
                    repo=Path(meta['repo']), input_path=Path(case['input_path']),
                    output_path=directory / 'output.txt', minsup=effective_minsup,
                    stats_path=directory / 'stats.toml')
                env = os.environ.copy()
                env['JULIA_NUM_THREADS'] = '1'
                measured = process_tools.run_process(argv, directory,
                    timeout_seconds=config['timeout_seconds'],
                    output_cap_bytes=config['output_cap_bytes'], rss_cap_bytes=config['rss_cap_bytes'],
                    poll_seconds=config['poll_seconds'], env=env)
                row = base | dict(attempt_id=attempt_id, repetition=repetition, variant=variant,
                                  spmf_ratio_mapping=mapping) | measured
                _json(directory / 'measurement.json', row)
                append_measurement(root / 'runs.csv', row)  # durable before validation
                slot_rows[(repetition, variant)] = row
                print(f"{scope} {case['dataset']} {case['minsup']} r{repetition} {variant}: {row['status']} {row['process_wall_seconds']:.3f}s", flush=True)
            directory = root / 'attempts' / row['attempt_id']
            validation_path = directory / 'validation.json'
            if validation_path.exists():
                verified = json.loads(validation_path.read_text(encoding='utf-8'))
            elif row['status'] != 'ok':
                verified = base | dict(ok=False, status=row['status'], attempt_id=row['attempt_id'])
                _json(validation_path, verified)
            else:
                process_tools.require_disk(root, config['minimum_free_disk_bytes'])
                canonical = evidence_dir / f'{repetition}-{variant}.canonical'
                # Interrupted validation may leave only a canonical owned by this
                # exact attempt. Do not reuse it without a durable validation row.
                if canonical.exists():
                    canonical.unlink()
                try:
                    info = validator.canonicalize(directory / 'output.txt', canonical,
                        evidence_dir / 'scratch', min_count=base['min_count'],
                        n_transactions=base['n_transactions'],
                        chunk_bytes=config['validation_chunk_bytes'], fan_in=config['validation_fan_in'],
                        scratch_cap_bytes=config['validation_scratch_cap_bytes'])
                    if variant == 'optimized' and (directory / 'stats.toml').exists():
                        with (directory / 'stats.toml').open('rb') as handle:
                            stats = tomllib.load(handle)
                        if stats['n_patterns'] != info['count'] or stats['min_count'] != base['min_count']:
                            raise ValueError('Julia stats disagree with validated count/threshold')
                    verified = base | info | dict(ok=True, status='ok', attempt_id=row['attempt_id'],
                                                   canonical=str(canonical.relative_to(root)))
                except (ValueError, OSError) as exc:
                    verified = base | dict(ok=False, status='validation_failed',
                                            error=str(exc), attempt_id=row['attempt_id'])
                _json(validation_path, verified)
            if verified.get('fingerprint') != meta['fingerprint']:
                raise ValueError('Validation provenance mismatch')
            validations[(repetition, variant)] = verified
        a, b = validations[(repetition, 'spmf')], validations[(repetition, 'optimized')]
        if repetition == 1 and a['ok'] and b['ok']:
            comparison_path = evidence_dir / 'comparison.json'
            if comparison_path.exists():
                comparison = json.loads(comparison_path.read_text(encoding='utf-8'))
            else:
                comparison = base | validator.compare_canonical(root / a['canonical'], root / b['canonical'])
                _json(comparison_path, comparison)
        elif repetition > 1:
            for variant in order:
                current, first = validations[(repetition, variant)], validations[(1, variant)]
                if current['ok'] and (not first['ok'] or current['canonical_sha256'] != first['canonical_sha256']
                                      or current['count'] != first['count']):
                    current.update(ok=False, status='validation_failed', error='Repeat digest/count differs')
                    _json(root / 'attempts' / current['attempt_id'] / 'validation.json', current)
        # Once validation evidence is durable, remove only this campaign's large
        # itemset files. Keep first canonical pair until condition is complete.
        for variant in order:
            info = validations[(repetition, variant)]
            if info['ok']:
                directory = root / 'attempts' / info['attempt_id']
                (directory / 'output.txt').unlink(missing_ok=True)
                if repetition > 1:
                    (root / info['canonical']).unlink(missing_ok=True)
    valid = bool(comparison and comparison['equal'] and all(v['ok'] for v in validations.values()))
    result = base | dict(equal=valid, count=validations[(1, 'spmf')].get('count'),
                         canonical_sha256=validations[(1, 'spmf')].get('canonical_sha256'),
                         repetitions=repetitions, comparison=comparison,
                         attempts=[v['attempt_id'] for v in validations.values()])
    _json(summary_path, result)
    for path in evidence_dir.glob('*.canonical'):
        path.unlink()
    return result


def fixture_expectations():
    return {'toy': {'count': 3, 'records': '1 #SUP: 4\n1 2 #SUP: 2\n2 #SUP: 3\n'},
            'boundary': {'count': 2, 'records': '1 #SUP: 7\n2 #SUP: 93\n'}}


def fixture_matches(name, result):
    expected = fixture_expectations()[name]
    digest = hashlib.sha256(expected['records'].encode('ascii')).hexdigest()
    return (result['equal'] and result['count'] == expected['count']
            and result.get('canonical_sha256') == digest)


def verify_sources(meta):
    for path, expected in meta.get('sources', {}).items():
        if not Path(path).is_file() or _hash(path) != expected:
            raise ValueError(f'Changed source during campaign: {path}')


def run_pilot(root, meta):
    fixtures = root / 'fixtures'
    fixtures.mkdir(exist_ok=True)
    toy = fixtures / 'toy.txt'
    toy.write_bytes(b'1 2\n1\n2\n1 2\n1\n')
    boundary = fixtures / 'boundary.txt'
    boundary.write_bytes(b'1\n' * 7 + b'2\n' * 93)
    cases = []
    for name, path, minsup in [('toy', toy, '0.4'), ('boundary', boundary, '0.07')]:
        info = inspect_input(path)
        cases.append(dict(dataset=name, input_path=str(path), minsup=minsup,
                          input_sha256=info['sha256'], n_transactions=info['n_transactions']))
    for name, levels in meta['config']['selected'].items():
        cases.append(meta['datasets'][name] | dict(dataset=name, minsup=levels[0]))
    for name in ('Chess', 'Mushroom'):
        cases.append(meta['datasets'][name] | dict(dataset=name,
                    minsup=meta['config']['selected'][name][-1]))
    results = []
    for case in cases:
        result = run_condition(root, meta, case, scope='pilot', repetitions=1)
        results.append(result)
        if case['dataset'] in fixture_expectations() and not fixture_matches(case['dataset'], result):
            result = result | dict(equal=False, fixture_error='Pair differs from hand-checked expected output')
            results[-1] = result
        if not result['equal']:
            break  # do not escalate workload while a mismatch is unresolved
    ok = len(results) == len(cases) and all(r['equal'] for r in results)
    report = dict(schema_version=1, fingerprint=meta['fingerprint'], ok=ok,
                  results=results, threshold_probe=threshold_info('0.07', 100),
                  spmf_ratio_mapping=spmf_ratio('0.07', 100),
                  note='Boundary exact ceil=7; documented CLI ratio encoding verified against hand-checked output')
    _json(root / 'pilot.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    for name in ('julia', 'java', 'jar', 'root'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--mode', choices=('preflight', 'pilot', 'main'), required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    args.root = args.root.resolve()
    meta = preflight(args.config.resolve(), repo, args.julia, args.java, args.jar)
    if args.resume:
        meta = check_resume(args.root, meta)
    else:
        args.root.mkdir(parents=True, exist_ok=False)
        _json(args.root / 'campaign.json', meta)
        snapshots = args.root / 'source'
        snapshots.mkdir()
        for index, source in enumerate(meta['sources']):
            (snapshots / f'{index:03d}-{Path(source).name}').write_bytes(Path(source).read_bytes())
    process_tools.require_disk(args.root, meta['config']['minimum_free_disk_bytes'])
    if args.mode == 'preflight':
        print(json.dumps(dict(fingerprint=meta['fingerprint'], datasets=meta['datasets']), indent=2))
        return 0
    if args.mode == 'pilot':
        return 0 if run_pilot(args.root, meta)['ok'] else 1
    require_pilot(args.root, meta['fingerprint'])
    results = []
    for dataset, levels in meta['config']['selected'].items():
        for minsup in levels:
            case = meta['datasets'][dataset] | dict(dataset=dataset, minsup=minsup)
            results.append(run_condition(args.root, meta, case, scope='main', repetitions=3))
    report = dict(fingerprint=meta['fingerprint'], complete=sum(r['equal'] for r in results),
                  total=35, conditions=results)
    _json(args.root / 'main.json', report)
    return 0 if report['complete'] == 35 else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f'Campaign stopped: {exc}', file=sys.stderr)
        raise SystemExit(1)
