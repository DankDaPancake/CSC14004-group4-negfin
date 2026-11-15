"""Sinh luật kết hợp X -> Y từ output negFIN (SPMF `a b #SUP: n`).

X, Y khác rỗng, rời nhau, X ∪ Y là frequent itemset. support = sup(X∪Y)/N,
confidence = sup(X∪Y)/sup(X), lift = confidence / (sup(Y)/N). Mọi tập con của một
frequent itemset cũng frequent nên sup(X), sup(Y) tra được ngay trong output.
"""
import argparse
import csv
import sys
import tomllib
from itertools import combinations


def read_itemsets(lines):
    supports = {}
    for line in lines:
        if line.strip():
            items, sup = line.split("#SUP:")
            supports[frozenset(map(int, items.split()))] = int(sup)
    return supports


def generate_rules(supports, n_transactions, minconf=0.0):
    """Trả về list dict, sắp theo lift giảm dần (hòa thì confidence, support, rồi X, Y)."""
    rules = []
    for z, sup_z in supports.items():
        for k in range(1, len(z)):
            for x in combinations(sorted(z), k):
                x = frozenset(x)
                y = z - x
                conf = sup_z / supports[x]
                if conf >= minconf:
                    rules.append(dict(antecedent=sorted(x), consequent=sorted(y), support_count=sup_z,
                                      support=sup_z / n_transactions, confidence=conf,
                                      lift=conf / (supports[y] / n_transactions)))
    rules.sort(key=lambda r: (-r["lift"], -r["confidence"], -r["support_count"], r["antecedent"], r["consequent"]))
    return rules


def diverse_top(rules, k):
    """Duyệt theo thứ tự lift, chỉ giữ luật không có sản phẩm nào đã xuất hiện ở luật được giữ trước đó."""
    used, picked = set(), []
    for r in rules:
        items = set(r["antecedent"]) | set(r["consequent"])
        if not items & used:
            picked.append(r)
            used |= items
            if len(picked) == k:
                break
    return picked


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--itemsets", required=True, help="output của run.jl")
    ap.add_argument("--stats", required=True, help="stats TOML của run.jl (lấy n_transactions)")
    ap.add_argument("--output", required=True, help="rules.csv")
    ap.add_argument("--minconf", type=float, default=0.5)
    ap.add_argument("--mapping", help="mapping.csv (id, ..., description) để in tên sản phẩm")
    ap.add_argument("--top", type=int, default=10)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # stdout bị pipe trên Windows mặc định cp1252
    if not 0 <= args.minconf <= 1:
        ap.error("--minconf phải trong [0, 1]")

    with open(args.stats, "rb") as f:
        n = tomllib.load(f)["n_transactions"]
    supports = read_itemsets(open(args.itemsets, encoding="utf-8"))
    rules = generate_rules(supports, n, args.minconf)
    names = {}
    if args.mapping:
        names = {int(r["id"]): r.get("description") or r.get("label") or r["id"]
                 for r in csv.DictReader(open(args.mapping, encoding="utf-8"))}

    def label(ids):
        return " + ".join(names.get(i, str(i)) for i in ids)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["antecedent", "consequent", "antecedent_names", "consequent_names",
                    "support_count", "support", "confidence", "lift"])
        for r in rules:
            w.writerow([" ".join(map(str, r["antecedent"])), " ".join(map(str, r["consequent"])),
                        label(r["antecedent"]), label(r["consequent"]), r["support_count"],
                        f"{r['support']:.6f}", f"{r['confidence']:.6f}", f"{r['lift']:.6f}"])

    print(f"N={n} itemsets={len(supports)} minconf={args.minconf} rules={len(rules)}")
    for title, rs in (("top theo lift", rules[:args.top]), ("top không trùng sản phẩm", diverse_top(rules, args.top))):
        print(f"\n# {title}")
        for r in rs:
            print(f"lift={r['lift']:6.2f} conf={r['confidence']:.2f} sup={r['support']:.4f} ({r['support_count']})  "
                  f"{label(r['antecedent'])}  =>  {label(r['consequent'])}")


if __name__ == "__main__":
    main()
