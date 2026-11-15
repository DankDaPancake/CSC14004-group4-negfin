import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("retail_rules", ROOT / "apps" / "retail" / "rules.py")
rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rules)

# data/toy/example.txt (N=5) ở minsup 0.4: kết quả negFIN đúng là file expected.
TOY = rules.read_itemsets(open(ROOT / "data" / "toy" / "example.expected.txt", encoding="utf-8"))


def find(rs, x, y):
    (r,) = [r for r in rs if r["antecedent"] == x and r["consequent"] == y]
    return r


class RuleTests(unittest.TestCase):
    def test_hand_computed_metrics(self):
        rs = rules.generate_rules(TOY, 5, minconf=0.0)
        r = find(rs, [2], [3])  # sup{2,3}=3, sup{2}=4, sup{3}=4
        self.assertEqual(r["support_count"], 3)
        self.assertAlmostEqual(r["support"], 0.6)
        self.assertAlmostEqual(r["confidence"], 0.75)
        self.assertAlmostEqual(r["lift"], 0.9375)
        r = find(rs, [5], [1, 2])  # sup{1,2,5}=2, sup{5}=4, sup{1,2}=2
        self.assertAlmostEqual(r["confidence"], 0.5)
        self.assertAlmostEqual(r["lift"], 1.25)

    def test_all_splits_and_minconf(self):
        rs = rules.generate_rules(TOY, 5, minconf=0.0)
        self.assertEqual(len(rs), 6 * 2 + 4 * 6 + 1 * 14)  # 2^k - 2 luật cho mỗi itemset k phần tử
        for r in rs:
            self.assertTrue(r["antecedent"] and r["consequent"])
            self.assertFalse(set(r["antecedent"]) & set(r["consequent"]))
        strict = rules.generate_rules(TOY, 5, minconf=0.8)
        self.assertTrue(all(r["confidence"] >= 0.8 for r in strict))
        self.assertNotIn(([2], [3]), [(r["antecedent"], r["consequent"]) for r in strict])

    def test_sorted_by_lift(self):
        lifts = [r["lift"] for r in rules.generate_rules(TOY, 5)]
        self.assertEqual(lifts, sorted(lifts, reverse=True))

    def test_diverse_top_has_disjoint_items(self):
        rs = rules.generate_rules(TOY, 5, minconf=0.0)
        top = rules.diverse_top(rs, 10)
        self.assertEqual(top[0], rs[0])
        seen = set()
        for r in top:
            items = set(r["antecedent"]) | set(r["consequent"])
            self.assertFalse(items & seen)
            seen |= items


if __name__ == "__main__":
    unittest.main()
