"""UCI Splice-junction (splice.data) -> SPMF transactions theo item "vị trí–base".

Vị trí -30..-1, +1..+30 (không có 0; điểm nối nằm giữa -1 và +1). Base mơ hồ (D, N, S, R)
không sinh item tại vị trí đó. ID cố định, không phụ thuộc dữ liệu: id = 4*chỉ_số_vị_trí + chỉ_số_base + 1.
"""
import argparse
import csv
from pathlib import Path

POSITIONS = [p for p in range(-30, 31) if p != 0]
BASES = "ACGT"
CLASSES = ("EI", "IE", "N")


def item_id(pos_index, base):
    return 4 * pos_index + BASES.index(base) + 1


def mapping_rows():
    return [(item_id(i, b), p, b, f"p{p:+d}_{b}") for i, p in enumerate(POSITIONS) for b in BASES]


def parse(lines):
    """Trả về list[(lớp, tên, transaction)] theo thứ tự file."""
    records = []
    for line in lines:
        if not line.strip():
            continue
        cls, name, seq = (f.strip() for f in line.split(","))
        if cls not in CLASSES or len(seq) != len(POSITIONS):
            raise ValueError(f"dòng không hợp lệ: {line!r}")
        records.append((cls, name, [item_id(i, b) for i, b in enumerate(seq.upper()) if b in BASES]))
    return records


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="splice.data")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--max-per-class", type=int, help="chỉ lấy N chuỗi đầu mỗi lớp (chạy thử)")
    args = ap.parse_args()

    records = parse(open(args.input, encoding="ascii"))
    if args.max_per_class:
        records = [r for c in CLASSES for r in [x for x in records if x[0] == c][:args.max_per_class]]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    def write(path, recs):
        path.write_text("".join(" ".join(map(str, t)) + "\n" for _, _, t in recs), newline="\n")

    write(out / "transactions_all.txt", records)
    for c in CLASSES:
        write(out / f"transactions_{c}.txt", [r for r in records if r[0] == c])
    with open(out / "labels.csv", "w", newline="") as f:  # dòng i của transactions_all <-> dòng i ở đây
        csv.writer(f, lineterminator="\n").writerows([("class", "name")] + [(c, n) for c, n, _ in records])
    with open(out / "mapping.csv", "w", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows([("id", "position", "base", "label")] + mapping_rows())

    counts = {c: sum(r[0] == c for r in records) for c in CLASSES}
    short = sum(len(t) < len(POSITIONS) for _, _, t in records)
    lines = [f"sequences={len(records)}"] + [f"class_{c}={n}" for c, n in counts.items()] + \
            [f"sequences_with_ambiguous_bases={short}"]
    (out / "prepare_report.txt").write_text("\n".join(lines) + "\n", newline="\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
