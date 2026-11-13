"""Render figures from the reported benchmark tables (requires matplotlib)."""
from pathlib import Path
import re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator, FuncFormatter

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "benchmark-baseline.md"
OUT = ROOT / "figures"


def number(value):
    return float(value.strip().replace('.', '').replace(',', '.'))


def table(section, end):
    text = SOURCE.read_text(encoding="utf-8").split(section, 1)[1].split(end, 1)[0]
    rows = []
    for line in text.splitlines():
        if line.startswith('|'):
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if cells[0] in {'Chess', 'Mushroom', 'Accidents', 'Retail', 'T10I4D100K'}:
                rows.append(cells)
    return rows


def interval(value):
    match = re.fullmatch(r'([\d.,]+)\s*\(([\d.,]+)–([\d.,]+)\)', value)
    if not match:
        raise ValueError(f"Invalid median and interval: {value}")
    return tuple(number(x) for x in match.groups())


def cold():
    rows = table('## Kết quả cold (median 3 lần)', '## Scalability')
    groups = list(dict.fromkeys(row[0] for row in rows))
    fig, axes = plt.subplots(2, len(groups), figsize=(17, 7), constrained_layout=True)
    for col, group in enumerate(groups):
        subset = [row for row in rows if row[0] == group]
        x = [float(row[1]) * 100 for row in subset]
        for axis, index, label, color in [(axes[0, col], 2, 'Thời gian (giây)', '#1768ac'),
                                          (axes[1, col], 3, 'Peak RSS (MiB)', '#bf5a36')]:
            values = [interval(row[index]) for row in subset]
            median = [v[0] for v in values]
            error = [[v[0] - v[1] for v in values], [v[2] - v[0] for v in values]]
            axis.errorbar(x, median, yerr=error, marker='o', markersize=3, capsize=2, color=color)
            axis.set_xscale('log')
            axis.invert_xaxis()
            axis.set_xticks([x[0], x[len(x) // 2], x[-1]])
            axis.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f'{value:g}'))
            axis.xaxis.set_minor_locator(NullLocator())
            axis.grid(alpha=.25)
            axis.set_xlabel('minsup (%) giảm →')
            if col == 0:
                axis.set_ylabel(label)
        axes[0, col].set_title(group)
    fig.suptitle('Baseline: cold median, khoảng min–max (3 lần)', fontsize=15)
    fig.savefig(OUT / 'cold-runtime-rss.png', dpi=160)
    plt.close(fig)


def scalability():
    rows = table('## Scalability', '## Nhận xét điểm nghẽn ban đầu')
    groups = list(dict.fromkeys(row[0] for row in rows))
    fig, axes = plt.subplots(2, len(groups), figsize=(12, 7), constrained_layout=True)
    for col, group in enumerate(groups):
        subset = [row for row in rows if row[0] == group]
        x = [number(row[3]) for row in subset]
        for axis, index, label, color in [(axes[0, col], 9, 'Cold wall (giây)', '#1768ac'),
                                          (axes[1, col], 10, 'Peak RSS (MiB)', '#bf5a36')]:
            axis.plot(x, [number(row[index]) for row in subset], marker='o', color=color)
            axis.set_xlabel('Số giao dịch (tiền tố)')
            if col == 0:
                axis.set_ylabel(label)
            axis.ticklabel_format(style='plain', axis='x')
            axis.grid(alpha=.25)
        axes[0, col].set_title(f'{group} · minsup {subset[0][1]}')
    fig.suptitle('Scalability: cold median (3 lần), 20–100% dữ liệu', fontsize=14)
    fig.savefig(OUT / 'scalability.png', dpi=160)
    plt.close(fig)


def workloads():
    rows = table('## Kết quả warm', '## Kết quả cold (median 3 lần)')
    groups = list(dict.fromkeys(row[0] for row in rows))
    selected = [min((r for r in rows if r[0] == g), key=lambda r: float(r[1])) for g in groups]
    labels = [f'{r[0]}\nminsup {r[1]}' for r in selected]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    positions = range(len(selected))
    for i, (index, label, color) in enumerate([(5, 'Normalize + prepare', '#5793c1'),
                                                (6, 'Build BMC', '#e79f44'),
                                                (7, 'Mine (count)', '#bb5f42')]):
        axes[0].bar([x + (i - 1) * .25 for x in positions],
                    [number(r[index]) for r in selected], width=.25, label=label, color=color)
    axes[0].set_yscale('log')
    axes[0].set_ylabel('Thời gian warm count (giây, log)')
    axes[0].legend(fontsize=8)
    axes[1].bar(positions, [number(r[3]) for r in selected], color='#557c6a')
    axes[1].set_yscale('log')
    axes[1].set_ylabel('Số mẫu (log)')
    for axis in axes:
        axis.set_xticks(list(positions), labels, fontsize=8)
        axis.grid(axis='y', alpha=.2)
    fig.suptitle('Workload tại minsup thấp nhất được chọn', fontsize=14)
    fig.savefig(OUT / 'workloads.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    cold()
    scalability()
    workloads()
