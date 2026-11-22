"""Vẽ hình cho Chương 3 từ output của pipeline ứng dụng (chạy notebook hoặc các lệnh trong
docs/applications-*-results.md trước). Ghi PDF (cho LaTeX) và PNG (cho bản Markdown) vào docs/report/figures/.

    python docs/report/ieee/figures.py --retail-rules results/apps/retail/full/rules_0.01_0.5.csv \
        --splice-dir results/apps/splice/full
"""
import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LogNorm  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "figures"
POSITIONS = [p for p in range(-30, 31) if p != 0]
BASES = "ACGT"
plt.rcParams.update({"pdf.fonttype": 42, "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8})


def save(fig, name):
    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{name}.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(OUT / f"{name}.pdf")


def rules_scatter(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    sup = [100 * float(r["support"]) for r in rows]
    conf = [float(r["confidence"]) for r in rows]
    lift = [float(r["lift"]) for r in rows]
    fig, ax = plt.subplots(figsize=(3.4, 2.4))
    sc = ax.scatter(sup, conf, c=lift, s=6, cmap="viridis", norm=LogNorm(), linewidths=0)
    ax.set_xlabel("support (% hóa đơn)")
    ax.set_ylabel("confidence")
    cbar = fig.colorbar(sc, ax=ax, label="lift (thang log)")
    cbar.set_ticks([5, 10, 20, 40, 80], labels=["5", "10", "20", "40", "80"])
    cbar.minorticks_off()
    ax.set_title(f"{len(rows)} luật, minsup 0,01, minconf 0,5")
    save(fig, "retail-rules")


def base_frequencies(path):
    """Tỷ lệ chuỗi có base b tại vị trí p, từ transaction (ID = 4j + b + 1)."""
    counts = [[0] * len(POSITIONS) for _ in BASES]
    n = 0
    for line in open(path, encoding="utf-8"):
        n += 1
        for item in map(int, line.split()):
            j, b = divmod(item - 1, 4)
            counts[b][j] += 1
    return [[c / n for c in row] for row in counts], n


def splice_heatmap(folder):
    fig, axes = plt.subplots(3, 1, figsize=(7.0, 3.6), sharex=True)
    im = None
    for ax, cls in zip(axes, ("EI", "IE", "N")):
        freq, n = base_frequencies(Path(folder) / f"transactions_{cls}.txt")
        im = ax.imshow(freq, aspect="auto", cmap="magma_r", vmin=0, vmax=1, interpolation="nearest")
        ax.set_yticks(range(4), list(BASES))
        ax.axvline(29.5, color="tab:blue", linewidth=1)  # điểm nối nằm giữa −1 và +1
        ax.set_ylabel(f"{cls}\n(n={n})")
    ticks = [i for i, p in enumerate(POSITIONS) if p in (-30, -20, -10, -5, -1, 5, 10, 20, 30)]
    axes[-1].set_xticks(ticks, [f"{POSITIONS[i]:+d}" for i in ticks])
    axes[-1].set_xlabel("vị trí so với điểm nối")
    fig.colorbar(im, ax=axes, label="tỷ lệ chuỗi trong lớp", fraction=0.025, pad=0.01)
    save(fig, "splice-positions")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--retail-rules", default="results/apps/retail/full/rules_0.01_0.5.csv")
    ap.add_argument("--splice-dir", default="results/apps/splice/full")
    args = ap.parse_args()
    rules_scatter(args.retail_rules)
    splice_heatmap(args.splice_dir)
