"""Summarize only verified, complete new SPMF/Julia cold pairs."""
import argparse
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics
import tempfile
import zipfile

_BENCH = Path(__file__).resolve().parents[2] / 'bench' / 'spmf_campaign.py'
_spec = importlib.util.spec_from_file_location('spmf_campaign_summary', _BENCH)
campaign = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(campaign)


def _read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def summarize(campaign_root: Path) -> tuple[list[dict], list[dict]]:
    root = Path(campaign_root)
    meta = _read(root / 'campaign.json')
    accepted, incomplete = [], []
    try:
        rows = campaign.read_measurements(root / 'runs.csv')
    except (ValueError, csv.Error) as exc:
        return [], [dict(dataset='campaign', minsup='', reason=str(exc))]
    for dataset, levels in meta['config']['selected'].items():
        for minsup in levels:
            point = dict(dataset=dataset, minsup=minsup)
            try:
                pair = [r for r in rows if r['scope'] == 'main'
                        and r['dataset'] == dataset and r['minsup'] == minsup]
                _require(len(pair) == 6, 'Need six main rows per paired point')
                _require(all(r['fingerprint'] == meta['fingerprint'] for r in pair),
                         'Mixed provenance')
                directory = root / 'conditions' / campaign._condition_id('main', point)
                condition = _read(directory / 'condition.json')
                comparison = _read(directory / 'comparison.json')
                _require(condition['fingerprint'] == comparison['fingerprint'] == meta['fingerprint'],
                         'Condition/comparison provenance mismatch')
                _require(condition['equal'] and condition['repetitions'] == 3,
                         'Condition not validated for three repetitions')
                _require(comparison['equal'] and all(comparison[k] == 0 for k in
                         ('missing', 'extra', 'support_mismatch')), 'Exact first-pair comparison failed')
                _require(set(condition['attempts']) == {r['attempt_id'] for r in pair},
                         'Condition attempt list differs')
                dataset_info = meta['datasets'][dataset]
                expected_input = (dataset_info['input_sha256'], str(dataset_info['n_transactions']),
                                  str(campaign.expected_min_count(minsup, dataset_info['n_transactions'])))
                validations = []
                staged = []
                for variant in ('spmf', 'optimized'):
                    group = [r for r in pair if r['variant'] == variant]
                    _require(len(group) == 3 and {int(r['repetition']) for r in group} == {1, 2, 3},
                             'Missing/duplicate repetitions')
                    walls, peaks = [], []
                    for row in group:
                        _require(row['status'] == 'ok' and int(row['exit_code']) == 0,
                                 'Non-successful measurement')
                        _require((row['input_sha256'], row['n_transactions'], row['min_count']) == expected_input,
                                 'Input/threshold mismatch')
                        run = root / 'attempts' / row['attempt_id']
                        measured = _read(run / 'measurement.json')
                        verified = _read(run / 'validation.json')
                        _require(verified['ok'] and verified['status'] == 'ok'
                                 and verified['fingerprint'] == meta['fingerprint']
                                 and verified['attempt_id'] == row['attempt_id'], 'Invalid validation evidence')
                        for key in ('variant', 'scope', 'dataset', 'minsup', 'repetition',
                                    'process_wall_seconds', 'maxrss_bytes', 'status'):
                            _require(str(measured[key]) == str(row[key]), f'Measurement CSV differs: {key}')
                        wall, peak = float(row['process_wall_seconds']), float(row['maxrss_bytes'])
                        _require(math.isfinite(wall) and wall > 0 and math.isfinite(peak) and peak > 0,
                                 'Invalid wall/RSS metric')
                        _require(verified['count'] == condition['count'], 'Pattern count differs')
                        _require(len(verified['canonical_sha256']) == 64, 'Invalid canonical digest')
                        validations.append(verified)
                        walls.append(wall)
                        peaks.append(peak / 1048576)
                    staged.append(point | dict(variant=variant, fingerprint=meta['fingerprint'],
                        input_sha256=expected_input[0], min_count=int(expected_input[2]),
                        n_transactions=int(expected_input[1]), n_patterns=condition['count'], repetitions=3,
                        wall_median_seconds=statistics.median(walls), wall_min_seconds=min(walls),
                        wall_max_seconds=max(walls), rss_median_mib=statistics.median(peaks),
                        rss_min_mib=min(peaks), rss_max_mib=max(peaks)))
                _require(len({v['canonical_sha256'] for v in validations}) == 1,
                         'Canonical repeat/variant digest differs')
                accepted.extend(staged)
            except (ValueError, KeyError, TypeError, OSError) as exc:
                incomplete.append(point | dict(reason=str(exc)))
    return accepted, incomplete


def package_campaign(root: Path, target: Path) -> dict:
    """Allowlist only reproducibility evidence; verify extracted bytes afresh."""
    root, target = Path(root).resolve(), Path(target).resolve()
    if target.exists():
        raise FileExistsError(target)
    files = []
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        allowed = (len(relative.parts) == 1 and path.suffix in ('.json', '.csv', '.md'))
        allowed |= (relative.parts[0] == 'source')
        allowed |= (relative.parts[0] == 'conditions' and path.suffix == '.json')
        allowed |= (relative.parts[0] == 'attempts' and path.name in
                    ('measurement.json', 'validation.json', 'stdout.log', 'stderr.log', 'stats.toml'))
        if allowed:
            files.append((path, relative.as_posix()))
    sums = ''.join(f'{campaign._hash(path)}  {name}\n' for path, name in files)
    target.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(target, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path, name in files:
            archive.write(path, name)
        archive.writestr('SHA256SUMS.txt', sums)
    with tempfile.TemporaryDirectory(prefix='spmf-package-verify-') as directory:
        with zipfile.ZipFile(target) as archive:
            if archive.testzip() is not None:
                raise ValueError('ZIP integrity failure')
            archive.extractall(directory)
        for line in sums.splitlines():
            digest, name = line.split('  ', 1)
            _require(campaign._hash(Path(directory) / name) == digest, 'Extracted checksum mismatch')
    return dict(path=str(target), sha256=campaign._hash(target), files=len(files))


def render_figures(rows, config, output: Path):
    """Print-ready figures, plus tabular CSV; call only with accepted summary."""
    if not rows:
        return []
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    colors = {'spmf': '#2a78d6', 'optimized': '#eb6834'}
    names = {'spmf': 'SPMF NegFIN', 'optimized': 'Julia Optimized'}
    markers = {'spmf': 'o', 'optimized': 's'}
    styles = {'spmf': '-', 'optimized': '--'}
    paths, captions = [], []
    plt.rcParams.update({'font.size': 10, 'text.color': '#0b0b0b',
        'axes.labelcolor': '#52514e', 'xtick.color': '#52514e', 'ytick.color': '#52514e',
        'axes.spines.top': False, 'axes.spines.right': False, 'figure.facecolor': '#fcfcfb',
        'axes.facecolor': '#fcfcfb', 'axes.edgecolor': '#c3c2b7'})

    def finish(fig, ax, stem, caption):
        ax.grid(axis='y', color='#e3e2dd', linewidth=.5)
        ax.set_axisbelow(True)
        fig.tight_layout()
        for suffix in ('png', 'pdf'):
            path = output / (stem + '.' + suffix)
            fig.savefig(path, dpi=180, bbox_inches='tight')
            paths.append(str(path))
        plt.close(fig)
        captions.append(f'**{stem}.** {caption}')

    for dataset, selected in config['selected'].items():
        points = [r for r in rows if r['dataset'] == dataset]
        if not points:
            continue
        fig, ax = plt.subplots(figsize=(7.2, 4.5))
        for variant in ('spmf', 'optimized'):
            by_level = {r['minsup']: r for r in points if r['variant'] == variant}
            # NaNs break lines at missing points rather than joining over failures.
            ordered = [by_level.get(level) for level in selected]
            x = [float(level) * 100 for level in selected]
            y = [r['wall_median_seconds'] if r else math.nan for r in ordered]
            low = [r['wall_median_seconds'] - r['wall_min_seconds'] if r else math.nan for r in ordered]
            high = [r['wall_max_seconds'] - r['wall_median_seconds'] if r else math.nan for r in ordered]
            ax.errorbar(x, y, yerr=[low, high], color=colors[variant],
                        marker=markers[variant], linestyle=styles[variant], markersize=6,
                        markeredgecolor='#fcfcfb', markeredgewidth=1.5, linewidth=1.5,
                        capsize=3, label=names[variant])
        ax.set(xlabel='Minimum support (%)', ylabel='Whole-process wall time (s)',
               title=f'{dataset}: cold process runtime')
        ax.invert_xaxis()
        ax.set_ylim(bottom=0)
        ax.legend(frameon=False)
        finish(fig, ax, f'spmf-julia-runtime-{dataset.lower()}',
               'Median of 3 new cold processes; whiskers show min–max. Includes startup/JIT/read/write; missing points are not measurements.')
        fig, ax = plt.subplots(figsize=(7.2, 4.5))
        by_level = {r['minsup']: r for r in points if r['variant'] == 'spmf'}
        x = [float(level) * 100 for level in selected]
        y = [by_level[level]['n_patterns'] if level in by_level else math.nan for level in selected]
        ax.plot(x, y, color=colors['spmf'], marker='o', markersize=6,
                markeredgecolor='#fcfcfb', linewidth=1.5)
        ax.set(xlabel='Minimum support (%)', ylabel='Frequent itemsets',
               title=f'{dataset}: verified itemset count (both implementations)')
        ax.invert_xaxis()
        ax.set_ylim(bottom=0)
        finish(fig, ax, f'spmf-julia-itemsets-{dataset.lower()}',
               'Exact itemset/support comparison on first paired outputs; repeat digests/counts match. Count is not a timing sample.')
    fig, ax = plt.subplots(figsize=(8.2, 4.7))
    labels = []
    for index, (dataset, selected) in enumerate(config['selected'].items()):
        middle = selected[3]
        labels.append(f'{dataset}\nminsup {middle}')
        for variant, offset in (('spmf', -.12), ('optimized', .12)):
            point = next((r for r in rows if r['dataset'] == dataset and
                          r['minsup'] == middle and r['variant'] == variant), None)
            if point:
                median = point['rss_median_mib']
                ax.errorbar(index + offset, median,
                    yerr=[[median - point['rss_min_mib']], [point['rss_max_mib'] - median]],
                    fmt=markers[variant], color=colors[variant], markersize=6, capsize=3,
                    label=names[variant] if index == 0 else None)
    ax.set_xticks(range(len(labels)), labels)
    ax.set(ylabel='Peak working set (MiB)', title='Peak RSS at fourth selected support level')
    ax.set_ylim(bottom=0)
    handles, legend_labels = ax.get_legend_handles_labels()
    if handles:
        ax.legend(frameon=False)
    finish(fig, ax, 'spmf-julia-rss-middle',
           'Median of 3 new cold processes; min–max whiskers. Native Windows peak working set includes runtime; Java heap is not RSS.')
    (output / 'captions.md').write_text('\n\n'.join(captions) + '\n', encoding='utf-8')
    with (output / 'figure-data.csv').open('x', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return paths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('campaign', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--package', action='store_true')
    parser.add_argument('--figures', action='store_true', help='Requires matplotlib; outputs PNG/PDF')
    args = parser.parse_args()
    accepted, incomplete = summarize(args.campaign)
    args.output.mkdir(parents=True, exist_ok=False)
    campaign._json(args.output / 'summary.json', dict(accepted=accepted, incomplete=incomplete))
    if accepted:
        with (args.output / 'summary.csv').open('x', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=list(accepted[0]))
            writer.writeheader()
            writer.writerows(accepted)
    if args.figures:
        meta = _read(args.campaign / 'campaign.json')
        render_figures(accepted, meta['config'], args.output / 'figures')
    if args.package:
        result = package_campaign(args.campaign, args.output / 'raw-evidence.zip')
        campaign._json(args.output / 'package.json', result)
    print(f'Accepted paired points: {len(accepted) // 2}; incomplete: {len(incomplete)}')
    return 0 if not incomplete else 1


if __name__ == '__main__':
    raise SystemExit(main())
