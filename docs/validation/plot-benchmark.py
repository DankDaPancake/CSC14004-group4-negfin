"""Render figures from raw benchmark runs and phases (requires matplotlib)."""
from pathlib import Path
import argparse
import collections
import csv
import math
import statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator, FuncFormatter

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures"


def aggregate_rows(rows, metric, *, scope, emit_mode):
    groups = collections.defaultdict(list)
    for row in rows:
        if row['scope'] != scope or row['emit_mode'] != emit_mode:
            continue
        if row.get('status') != 'ok' or not row.get(metric):
            raise ValueError(f'Missing or failed measurement: {row.get("dataset")} {row.get("minsup")}')
        value = float(row[metric])
        if not math.isfinite(value) or value < 0:
            raise ValueError(f'Invalid {metric}: {row[metric]}')
        groups[(row['dataset'], row['minsup'], row['fraction'])].append(value)
    return {key: (statistics.median(values), min(values), max(values), len(values))
            for key, values in groups.items()}


def read_raw(run_dir):
    def read(name):
        with (run_dir / name).open(encoding='utf-8-sig', newline='') as stream:
            return list(csv.DictReader(stream))
    runs, phases = read('runs.csv'), read('phases.csv')
    fields = ('run_id', 'variant', 'scope', 'dataset', 'fraction', 'minsup', 'emit_mode', 'repetition')
    index = {tuple(row[k] for k in fields): row for row in runs}
    if len(index) != len(runs):
        raise ValueError('Duplicate run key')
    for row in phases:
        key = tuple(row[k] for k in fields)
        if key not in index:
            raise ValueError(f'Phase without run: {key}')
        row['status'] = index[key]['status']
    return runs, phases


def raw_figures(run_dir):
    runs, phases = read_raw(run_dir)
    cold_wall = aggregate_rows(runs, 'process_wall_seconds', scope='cold', emit_mode='cli')
    cold_rss = aggregate_rows(runs, 'maxrss_bytes', scope='cold', emit_mode='cli')
    groups = ['Chess', 'Mushroom', 'Accidents', 'Retail', 'T10I4D100K']
    if (len(cold_wall) != 35 or set(cold_wall) != set(cold_rss)
            or any(v[3] != 3 for v in [*cold_wall.values(), *cold_rss.values()])):
        raise ValueError('Expected 35 cold configurations with runtime and RSS')
    fig, axes = plt.subplots(2, len(groups), figsize=(17, 7), constrained_layout=True)
    for col, group in enumerate(groups):
        keys = sorted((k for k in cold_wall if k[0] == group), key=lambda k: -float(k[1]))
        if len(keys) != 7:
            raise ValueError(f'Expected 7 thresholds for {group}')
        x = [float(k[1]) * 100 for k in keys]
        for axis, source, scale, label, color in [(axes[0, col], cold_wall, 1, 'Thời gian (giây)', '#1768ac'),
                                                  (axes[1, col], cold_rss, 2**20, 'Peak RSS (MiB)', '#bf5a36')]:
            values = [source[k] for k in keys]
            median = [v[0] / scale for v in values]
            errors = [[(v[0]-v[1])/scale for v in values], [(v[2]-v[0])/scale for v in values]]
            axis.errorbar(x, median, yerr=errors, marker='o', markersize=3, capsize=2, color=color)
            axis.set_xscale('log'); axis.invert_xaxis()
            axis.set_xticks([x[0], x[len(x)//2], x[-1]])
            axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:g}'))
            axis.xaxis.set_minor_locator(NullLocator()); axis.grid(alpha=.25)
            axis.set_xlabel('minsup (%) giảm →')
            if col == 0: axis.set_ylabel(label)
        axes[0, col].set_title(group)
    fig.suptitle('Baseline: cold median, khoảng min–max (3 lần)', fontsize=15)
    fig.savefig(OUT / 'cold-runtime-rss.png', dpi=160); plt.close(fig)

    wall = aggregate_rows(runs, 'process_wall_seconds', scope='scalability-cold', emit_mode='cli')
    rss = aggregate_rows(runs, 'maxrss_bytes', scope='scalability-cold', emit_mode='cli')
    fig, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
    for col, group in enumerate(['Accidents', 'T10I4D100K']):
        keys = sorted((k for k in wall if k[0] == group), key=lambda k: float(k[2]))
        if (len(keys) != 5 or any(k not in rss for k in keys)
                or any(wall[k][3] != 3 or rss[k][3] != 3 for k in keys)):
            raise ValueError(f'Expected 5 scalability configurations for {group}')
        x = [int(next(r['n_transactions'] for r in runs if r['scope'] == 'scalability-cold'
                      and (r['dataset'], r['minsup'], r['fraction']) == k)) for k in keys]
        for axis, source, scale, label, color in [(axes[0, col], wall, 1, 'Cold wall (giây)', '#1768ac'),
                                                  (axes[1, col], rss, 2**20, 'Peak RSS (MiB)', '#bf5a36')]:
            v = [source[k] for k in keys]
            axis.errorbar(x, [a[0]/scale for a in v], yerr=[[(a[0]-a[1])/scale for a in v],
                          [(a[2]-a[0])/scale for a in v]], marker='o', capsize=3, color=color)
            axis.set_xlabel('Số giao dịch (tiền tố)'); axis.grid(alpha=.25)
            if col == 0: axis.set_ylabel(label)
            axis.ticklabel_format(style='plain', axis='x')
        axes[0, col].set_title(f'{group} · minsup {keys[0][1]}')
    fig.suptitle('Scalability: cold median, min–max (3 lần), 20–100% dữ liệu', fontsize=14)
    fig.savefig(OUT / 'scalability.png', dpi=160); plt.close(fig)

    # Phase timings are medians from the raw long-form table. Normalize and
    # prepare are paired by repetition before computing their sum's median.
    count_runs = [r for r in runs if r['scope'] == 'warm' and r['emit_mode'] == 'count']
    selected = {g: min((r for r in count_runs if r['dataset'] == g), key=lambda r: float(r['minsup']))
                for g in groups}
    labels = [f'{g}\nminsup {selected[g]["minsup"]}' for g in groups]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    positions = range(len(groups)); phase_values = []
    for group in groups:
        subset = [r for r in phases if r['scope'] == 'warm' and r['emit_mode'] == 'count'
                  and r['dataset'] == group and r['minsup'] == selected[group]['minsup']]
        by_rep = collections.defaultdict(dict)
        for r in subset:
            if r['status'] != 'ok': raise ValueError('Failed phase run')
            if r['phase'] in by_rep[r['repetition']]: raise ValueError('Duplicate phase in run')
            by_rep[r['repetition']][r['phase']] = float(r['seconds'])
        required = {'normalize', 'prepare', 'build_bmc', 'collect_nodesets', 'mine'}
        if len(by_rep) not in (3, 5) or any(set(v) != required for v in by_rep.values()):
            raise ValueError(f'Unexpected phases or repetitions for {group}')
        phase_values.append([statistics.median(v['normalize']+v['prepare'] for v in by_rep.values()),
                             statistics.median(v['build_bmc'] for v in by_rep.values()),
                             statistics.median(v['mine'] for v in by_rep.values())])
    for i, (label, color) in enumerate([('Normalize + prepare', '#5793c1'), ('Build BMC', '#e79f44'), ('Mine (count)', '#bb5f42')]):
        axes[0].bar([x+(i-1)*.25 for x in positions], [v[i] for v in phase_values], width=.25, label=label, color=color)
    axes[0].set_yscale('log'); axes[0].set_ylabel('Thời gian warm count (giây, log)'); axes[0].legend(fontsize=8)
    axes[1].bar(positions, [int(selected[g]['n_patterns']) for g in groups], color='#557c6a')
    axes[1].set_yscale('log'); axes[1].set_ylabel('Số mẫu (log)')
    for axis in axes:
        axis.set_xticks(list(positions), labels, fontsize=8); axis.grid(axis='y', alpha=.2)
    fig.suptitle('Workload tại minsup thấp nhất được chọn', fontsize=14)
    fig.savefig(OUT / 'workloads.png', dpi=160); plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot raw benchmark run and phase CSVs')
    parser.add_argument('run_dir', type=Path, help='directory containing runs.csv and phases.csv')
    args = parser.parse_args()
    OUT.mkdir(exist_ok=True)
    raw_figures(args.run_dir)
