import importlib.util
import unittest
from pathlib import Path

import pandas as pd

APPS = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


retail = load("retail_prepare", APPS / "retail" / "prepare.py")
splice = load("splice_prepare", APPS / "splice" / "prepare.py")


class RetailTests(unittest.TestCase):
    def rows(self):
        t = pd.Timestamp
        return pd.DataFrame([
            # InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice
            ("2", "85123a", "HEART", 1, t("2011-01-02"), 2.5),   # mã chữ thường gộp với 85123A
            ("2", "85123A", "HEART", 3, t("2011-01-02"), 2.5),   # trùng trong hóa đơn -> 1 item
            ("2", "POST", "POSTAGE", 1, t("2011-01-02"), 18.0),  # không phải sản phẩm
            ("1", "22423", "CAKESTAND", 1, t("2011-01-01"), 12.0),
            ("1", "85123A", None, 1, t("2011-01-01"), 2.5),
            ("C3", "22423", "CAKESTAND", -1, t("2011-01-03"), 12.0),  # hủy
            ("A4", "B", "Adjust bad debt", 1, t("2011-01-03"), 11062.0),
            ("5", "22423", "CAKESTAND", -5, t("2011-01-04"), 0.0),    # quantity âm, giá 0
        ], columns=["InvoiceNo", "StockCode", "Description", "Quantity", "InvoiceDate", "UnitPrice"])

    def test_filters_and_mapping(self):
        tx, mapping, report = retail.build_transactions(self.rows())
        self.assertEqual(list(mapping.stock_code), ["22423", "85123A"])
        self.assertEqual(list(mapping.id), [1, 2])
        self.assertEqual(list(mapping.description), ["CAKESTAND", "HEART"])
        self.assertEqual(list(mapping.n_invoices), [1, 2])
        self.assertEqual(tx, [[1, 2], [2]])  # hóa đơn 1 trước hóa đơn 2 theo thời gian
        self.assertEqual(report[0][1:], (8, 5))
        self.assertEqual(report[-1][2], 2)

    def test_sample_takes_earliest_invoices(self):
        tx, mapping, _ = retail.build_transactions(self.rows(), max_transactions=1)
        self.assertEqual(tx, [[1, 2]])


class SpliceTests(unittest.TestCase):
    def test_fixed_mapping(self):
        rows = splice.mapping_rows()
        self.assertEqual(len(rows), 240)
        self.assertEqual(rows[0], (1, -30, "A", "p-30_A"))
        self.assertEqual(rows[-1], (240, 30, "T", "p+30_T"))
        self.assertEqual([r[0] for r in rows], list(range(1, 241)))

    def test_parse_skips_ambiguous_bases(self):
        seq = "A" * 29 + "N" + "GT" + "C" * 28
        (cls, name, tx), = splice.parse([f"EI,  X-DONOR-1,   {seq}\n", "\n"])
        self.assertEqual((cls, name, len(tx)), ("EI", "X-DONOR-1", 59))
        labels = {r[0]: r[3] for r in splice.mapping_rows()}
        self.assertIn("p+1_G", [labels[i] for i in tx])
        self.assertIn("p+2_T", [labels[i] for i in tx])
        self.assertNotIn(-1, [r[1] for r in splice.mapping_rows() if r[0] in tx])

    def test_rejects_bad_rows(self):
        with self.assertRaises(ValueError):
            splice.parse(["XX, a, " + "A" * 60])
        with self.assertRaises(ValueError):
            splice.parse(["EI, a, " + "A" * 59])


if __name__ == "__main__":
    unittest.main()
