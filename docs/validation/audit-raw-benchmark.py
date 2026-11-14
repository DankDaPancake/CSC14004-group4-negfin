"""Check run/phase/summary consistency; run with the handoff run directory."""
import collections
import csv
import math
from pathlib import Path
import statistics
import sys

if len(sys.argv) != 2:
    raise SystemExit('Usage: python audit-raw-benchmark.py <run-directory>')
run_dir = Path(sys.argv[1])


def read(name):
    with (run_dir / name).open(encoding='utf-8-sig', newline='') as source:
        return list(csv.DictReader(source))


runs, phases, summary = (read(name) for name in ('runs.csv', 'phases.csv', 'summary.csv'))
dimensions = ['variant', 'scope', 'dataset', 'fraction', 'minsup', 'emit_mode']
run_key = ['run_id', *dimensions, 'repetition']
run_counts = collections.Counter(tuple(row[k] for k in run_key) for row in runs)
phase_counts = collections.Counter(tuple(row[k] for k in run_key) for row in phases)
phase_names = collections.defaultdict(list)
for row in phases:
    phase_names[tuple(row[k] for k in run_key)].append(row['phase'])
groups = collections.defaultdict(list)
for row in runs:
    if row['status'] == 'ok':
        for metric in ('phases_total_seconds', 'process_wall_seconds', 'maxrss_bytes'):
            if row[metric]:
                groups[tuple(row[k] for k in dimensions) + ('', metric)].append(float(row[metric]))
for row in phases:
    for metric in ('seconds', 'bytes', 'gc_seconds'):
        if row[metric]:
            groups[tuple(row[k] for k in dimensions) + (row['phase'], metric)].append(float(row[metric]))

errors = []
if any(count != 1 for count in run_counts.values()):
    errors.append('duplicate run key')
if set(run_counts) != set(phase_counts) or any(count != 5 for count in phase_counts.values()):
    errors.append('phase/run keys or phase row counts differ')
required = {'normalize', 'prepare', 'build_bmc', 'collect_nodesets', 'mine'}
if any(set(names) != required or len(names) != len(set(names)) for names in phase_names.values()):
    errors.append('invalid phase names')
seen = set()
for row in summary:
    key = tuple(row[k] for k in dimensions) + (row['phase'], row['metric'])
    if key in seen:
        errors.append(f'duplicate summary key: {key}')
    seen.add(key)
    values = groups.get(key, [])
    if not values:
        errors.append(f'summary without values: {key}')
        continue
    actual = {'median': statistics.median(values), 'min': min(values),
              'max': max(values), 'n': len(values)}
    for metric, value in actual.items():
        if not math.isclose(float(row[metric]), value, rel_tol=1e-11, abs_tol=1e-9):
            errors.append(f'{key}: {metric} differs')
if set(groups) != seen:
    errors.append('summary does not cover every computed group')
print(f'{len(runs)} runs; statuses: {dict(collections.Counter(row["status"] for row in runs))}; '
      f'{len(phases)} phase rows; {len(summary)} summary rows; {len(errors)} errors')
for error in errors[:20]:
    print(error)
if errors:
    raise SystemExit(1)
