"""So pattern negFIN của một lớp splice với các lớp còn lại.

Với mỗi itemset của lớp đích: support (tỷ lệ) trong từng lớp EI/IE/N, đếm trực tiếp từ transaction,
và growth = support_lớp_đích / support_các_lớp_khác_gộp (inf nếu lớp khác không có).
Mẫu số mỗi lớp = số chuỗi của lớp đó.
"""
import argparse
import csv
import math
import sys
from pathlib import Path

CLASSES = ("EI", "IE", "N")


def read_transactions(path):
    return [frozenset(map(int, line.split())) for line in open(path, encoding="utf-8")]


def read_itemsets(path):
    for line in open(path, encoding="utf-8"):
        if line.strip():
            items, sup = line.split("#SUP:")
            yield frozenset(map(int, items.split())), int(sup)


def compare(itemsets, by_class, target):
    """itemsets: [(frozenset, support_count trong target)]; by_class: {lớp: [transaction]}."""
    rows = []
    rest = [t for c, ts in by_class.items() if c != target for t in ts]
    for items, sup in itemsets:
        frac = {c: sum(items <= t for t in ts) / len(ts) for c, ts in by_class.items()}
        if round(frac[target] * len(by_class[target])) != sup:
            raise ValueError(f"support của {sorted(items)} không khớp transaction lớp {target}")
        rest_frac = sum(items <= t for t in rest) / len(rest)
        rows.append(dict(items=sorted(items), support=frac, rest=rest_frac,
                         growth=frac[target] / rest_frac if rest_frac else math.inf))
    rows.sort(key=lambda r: (-r["growth"], -r["support"][target], -len(r["items"]), r["items"]))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--target", required=True, choices=CLASSES)
    ap.add_argument("--itemsets", required=True, help="output run.jl cho transactions_<target>.txt")
    ap.add_argument("--data", required=True, help="thư mục output của prepare.py")
    ap.add_argument("--output", required=True, help="compare.csv")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # stdout bị pipe trên Windows mặc định cp1252

    data = Path(args.data)
    by_class = {c: read_transactions(data / f"transactions_{c}.txt") for c in CLASSES}
    label = {int(r["id"]): r["label"] for r in csv.DictReader(open(data / "mapping.csv", encoding="utf-8"))}
    rows = compare(list(read_itemsets(args.itemsets)), by_class, args.target)

    def name(ids):
        return " + ".join(label[i] for i in sorted(ids, key=lambda i: (int(label[i][1:].split("_")[0]), i)))

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["items", "labels", "length"] + [f"support_{c}" for c in CLASSES] + ["support_rest", "growth"])
        for r in rows:
            w.writerow([" ".join(map(str, r["items"])), name(r["items"]), len(r["items"])]
                       + [f"{r['support'][c]:.4f}" for c in CLASSES] + [f"{r['rest']:.4f}", f"{r['growth']:.2f}"])

    print(f"target={args.target} itemsets={len(rows)} " + " ".join(f"N_{c}={len(t)}" for c, t in by_class.items()))
    for r in rows[:args.top]:
        s = r["support"]
        print(f"growth={r['growth']:7.2f}  EI={s['EI']:.1%} IE={s['IE']:.1%} N={s['N']:.1%}  {name(r['items'])}")


if __name__ == "__main__":
    main()
