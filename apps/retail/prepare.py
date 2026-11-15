"""UCI Online Retail (.xlsx) -> SPMF transactions + StockCode mapping.

Một giao dịch = một hóa đơn (InvoiceNo); item = StockCode sản phẩm, ánh xạ sang ID nguyên dương.
Chính sách lọc: xem docs/applications-proposal.md.
"""
import argparse
import re
from pathlib import Path

import pandas as pd

PRODUCT_CODE = re.compile(r"^\d{5}[A-Z]*$")  # 85123A; loại POST, DOT, M, BANK CHARGES, gift_*, DCGS*...


def build_transactions(df, max_transactions=None):
    """Trả về (transactions: list[list[int]], mapping: DataFrame, report: list[(bước, số dòng, số hóa đơn)])."""
    df = df.copy()
    df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
    df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()
    report = [("raw", len(df), df["InvoiceNo"].nunique())]

    def step(name, keep):
        nonlocal df
        df = df[keep]
        report.append((name, len(df), df["InvoiceNo"].nunique()))

    step("bo_hoa_don_huy_dieu_chinh (C*, A*)", df["InvoiceNo"].str.fullmatch(r"\d+"))
    step("bo_quantity_<=0", df["Quantity"] > 0)
    step("bo_unitprice_<=0", df["UnitPrice"] > 0)
    step("chi_giu_ma_san_pham", df["StockCode"].str.match(PRODUCT_CODE))

    if max_transactions is not None:
        first = df.groupby("InvoiceNo")["InvoiceDate"].min().sort_values(kind="stable")
        step(f"mau_{max_transactions}_hoa_don_dau", df["InvoiceNo"].isin(first.index[:max_transactions]))

    codes = sorted(df["StockCode"].unique())
    code_id = {c: i for i, c in enumerate(codes, start=1)}
    desc = (df.dropna(subset=["Description"])
              .assign(Description=lambda d: d["Description"].astype(str).str.strip())
              .groupby("StockCode")["Description"]
              .agg(lambda s: s.value_counts().index[0]))  # mô tả phổ biến nhất của mã
    n_inv = df.groupby("StockCode")["InvoiceNo"].nunique()
    mapping = pd.DataFrame({"id": [code_id[c] for c in codes], "stock_code": codes,
                            "description": [desc.get(c, "") for c in codes],
                            "n_invoices": [int(n_inv[c]) for c in codes]})

    df = df.sort_values(["InvoiceDate", "InvoiceNo"], kind="stable")
    transactions = [sorted({code_id[c] for c in g}) for _, g in df.groupby("InvoiceNo", sort=False)["StockCode"]]
    return transactions, mapping, report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True, help="Online Retail.xlsx")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--max-transactions", type=int, help="chỉ lấy N hóa đơn sớm nhất (chạy thử)")
    args = ap.parse_args()

    df = pd.read_excel(args.input, dtype={"InvoiceNo": str, "StockCode": str})
    transactions, mapping, report = build_transactions(df, args.max_transactions)

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "transactions.txt").write_text("".join(" ".join(map(str, t)) + "\n" for t in transactions), newline="\n")
    mapping.to_csv(out / "mapping.csv", index=False, lineterminator="\n")
    lines = [f"{name}\trows={rows}\tinvoices={inv}" for name, rows, inv in report]
    lines += [f"transactions={len(transactions)}", f"items={len(mapping)}",
              f"avg_items_per_transaction={sum(map(len, transactions)) / max(len(transactions), 1):.2f}"]
    (out / "prepare_report.txt").write_text("\n".join(lines) + "\n", newline="\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
