import importlib.util
import math
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "splice_compare", Path(__file__).resolve().parents[1] / "splice" / "compare.py")
cmp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cmp)

F = frozenset
BY_CLASS = {
    "EI": [F({1, 2}), F({1, 2, 3}), F({1}), F({3})],  # {1,2}: 2/4
    "IE": [F({1, 2}), F({3}), F({3}), F({3})],        # {1,2}: 1/4
    "N": [F({3}), F({3}), F({1}), F({2})],            # {1,2}: 0/4
}


class CompareTests(unittest.TestCase):
    def test_support_per_class_and_growth(self):
        rows = cmp.compare([(F({1, 2}), 2), (F({1}), 3)], BY_CLASS, "EI")
        r = next(r for r in rows if r["items"] == [1, 2])
        self.assertEqual(r["support"], {"EI": 0.5, "IE": 0.25, "N": 0.0})
        self.assertAlmostEqual(r["rest"], 1 / 8)
        self.assertAlmostEqual(r["growth"], 4.0)  # 0.5 / (1/8)
        r1 = next(r for r in rows if r["items"] == [1])  # EI 3/4, rest 2/8
        self.assertAlmostEqual(r1["growth"], 3.0)
        self.assertEqual(rows[0]["items"], [1, 2])  # growth cao hơn đứng trước

    def test_infinite_growth_and_mismatch(self):
        only = {"EI": [F({9})], "IE": [F({1})], "N": [F({1})]}
        (r,) = cmp.compare([(F({9}), 1)], only, "EI")
        self.assertTrue(math.isinf(r["growth"]))
        with self.assertRaises(ValueError):
            cmp.compare([(F({1, 2}), 3)], BY_CLASS, "EI")


if __name__ == "__main__":
    unittest.main()
