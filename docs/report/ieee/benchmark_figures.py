"""Render the Chapter 2 panels from the two benchmark handoffs."""
import argparse
import csv
from pathlib import Path
from statistics import median

from figures import plt, save

DATASETS = ("Chess", "Mushroom", "Retail", "Accidents", "T10I4D100K")
SPMF_VARIANTS = (("spmf", "SPMF", "tab:blue", "o"), ("optimized", "Julia Optimized", "tab:orange", "s"))
SCALE_VARIANTS = (("baseline", "Julia Baseline", "tab:blue", "o"), SPMF_VARIANTS[1])


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def errorbar(ax, x, rows, key, variant):
    _, label, color, marker = variant
    mid = [float(row[f"{key}_median_{unit(key)}"]) for row in rows]
    lo = [float(row[f"{key}_min_{unit(key)}"]) for row in rows]
    hi = [float(row[f"{key}_max_{unit(key)}"]) for row in rows]
    ax.errorbar(x, mid, yerr=[[a - b for a, b in zip(mid, lo)], [a - b for a, b in zip(hi, mid)]],
                label=label, color=color, marker=marker, markersize=3.5, capsize=2, linewidth=1.1)


def unit(key):
    return "seconds" if key == "wall" else "mib"


def comparison_figures(rows):
    if len(rows) != 70 or any(row["repetitions"] != "3" for row in rows):
        raise ValueError("Expected 70 series rows, with three repetitions each")
    if len({row["fingerprint"] for row in rows}) != 1:
        raise ValueError("Mixed benchmark campaigns")
    middle = {variant[0]: [] for variant in SPMF_VARIANTS}
    for dataset in DATASETS:
        groups = {variant[0]: sorted(
            (r for r in rows if r["dataset"] == dataset and r["variant"] == variant[0]),
            key=lambda r: float(r["minsup"]), reverse=True)
            for variant in SPMF_VARIANTS}
        s, j = groups["spmf"], groups["optimized"]
        keys = ("minsup", "input_sha256", "min_count", "n_patterns")
        if (len(s) != 7 or len({r["minsup"] for r in s}) != 7
                or [tuple(r[k] for k in keys) for r in s] != [tuple(r[k] for k in keys) for r in j]):
            raise ValueError(f"Unpaired conditions for {dataset}")
        x = list(range(7))
        labels = [r["minsup"].replace(".", ",") for r in s]
        fig, (wall, patterns) = plt.subplots(1, 2, figsize=(7.05, 2.35), layout="constrained")
        for variant in SPMF_VARIANTS:
            errorbar(wall, x, groups[variant[0]], "wall", variant)
            middle[variant[0]].append(groups[variant[0]][3])
        wall.set_title("(a) Thời gian toàn tiến trình")
        wall.set_ylabel("Thời gian (giây, log)")
        wall.legend(loc="best")
        patterns.plot(x, [int(r["n_patterns"]) for r in s], color="tab:green", marker="D", markersize=3.5)
        patterns.set_title("(b) Số itemset khớp")
        patterns.set_ylabel("Itemset (log)")
        for ax in (wall, patterns):
            ax.set_xticks(x, labels)
            ax.set_xlabel("Minsup")
            ax.set_yscale("log")
            ax.grid(axis="y", alpha=.3)
        save(fig, f"benchmark-{dataset.lower()}")

    fig, ax = plt.subplots(figsize=(7.05, 2.3), layout="constrained")
    for (variant, shift) in zip(SPMF_VARIANTS, (-.1, .1)):
        errorbar(ax, [x + shift for x in range(len(DATASETS))], middle[variant[0]], "rss", variant)
    ax.set_xticks(range(len(DATASETS)), DATASETS)
    ax.set_xlim(-.45, 4.45)
    ax.set_ylim(bottom=0)
    ax.set_ylabel("Peak working set (MiB)")
    ax.grid(axis="y", alpha=.3)
    ax.legend()
    save(fig, "benchmark-rss")


def scalability_figure(root):
    rows = [r for path in sorted(root.glob("*/runs.csv")) for r in read_rows(path)
            if r["scope"] == "scalability-cold" and r["status"] == "ok"]
    fractions = (.1, .25, .5, .75, 1.)
    fig, axes = plt.subplots(2, 2, figsize=(7.05, 4.0), layout="constrained")
    for col, (dataset, minsup) in enumerate((("Accidents", "0.25"), ("T10I4D100K", "0.004"))):
        hashes = {}
        for variant, label, color, marker in SCALE_VARIANTS:
            wall, rss = [], []
            for fraction in fractions:
                group = [r for r in rows if r["dataset"] == dataset and r["minsup"] == minsup
                         and r["variant"] == variant and float(r["fraction"]) == fraction]
                if len(group) != 3 or {r["repetition"] for r in group} != {"1", "2", "3"}:
                    raise ValueError(f"Expected three cold repetitions for {dataset} {fraction} {variant}")
                digests = {r["input_sha256"] for r in group}
                if len(digests) != 1 or hashes.setdefault(fraction, digests) != digests:
                    raise ValueError(f"Input hash mismatch for {dataset} {fraction}")
                wall.append(median(float(r["process_wall_seconds"]) for r in group))
                rss.append(median(float(r["maxrss_bytes"]) / 2**20 for r in group))
            for ax, y in zip(axes[:, col], (wall, rss)):
                ax.plot(fractions, y, color=color, marker=marker, markersize=3.5, label=label)
        axes[0, col].set_title(f"{dataset} (minsup {minsup.replace('.', ',')})")
        for ax, ylabel in zip(axes[:, col], ("Cold wall (giây)", "Peak RSS (MiB)")):
            ax.set_xticks(fractions, [f"{x:.0%}" for x in fractions])
            ax.set_ylabel(ylabel)
            ax.grid(axis="y", alpha=.3)
        axes[1, col].set_xlabel("Tỷ lệ giao dịch giữ lại")
    axes[0, 0].legend()
    save(fig, "benchmark-scalability")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--comparison", type=Path, required=True, help="SPMF–Julia figure-data.csv")
    parser.add_argument("--paired-runs", type=Path, required=True, help="Baseline–Optimized full-run directory")
    args = parser.parse_args()
    comparison_figures(read_rows(args.comparison))
    scalability_figure(args.paired_runs)
