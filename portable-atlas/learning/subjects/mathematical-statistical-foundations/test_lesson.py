from fractions import Fraction
from itertools import product
import unittest
from lesson import calculate, PRESETS


class ProbabilityTest(unittest.TestCase):
    def test_independent_hand_count(self):
        # Literally hand-labelled 12 members, not generated from the production counts.
        members = ["A+", "A+", "A-", "B+", "B+", "B+", "B-", "B-", "B-", "B-", "B-", "B-"]
        counts = {"ap": members.count("A+"), "an": members.count("A-"),
                  "bp": members.count("B+"), "bn": members.count("B-")}
        row = calculate(counts)
        expected = {"prior": "1/4", "sensitivity": "2/3", "false_positive_rate": "1/3",
                    "positive_rate": "5/12", "ppv": "2/5"}
        self.assertEqual({k:v["fraction"] for k,v in row["probabilities"].items()}, expected)
        self.assertEqual(row["bayes"]["posterior"], "2/5")

    def test_prior_changes_ppv_at_fixed_rates(self):
        rare = calculate(PRESETS["rare"])["probabilities"]
        balanced = calculate(PRESETS["balanced"])["probabilities"]
        for key in ("sensitivity", "false_positive_rate"):
            self.assertEqual(rare[key]["fraction"], balanced[key]["fraction"])
        self.assertEqual(rare["sensitivity"]["fraction"], "9/10")
        self.assertEqual(rare["false_positive_rate"]["fraction"], "1/10")
        self.assertEqual(rare["ppv"]["fraction"], "1/12")
        self.assertEqual(balanced["ppv"]["fraction"], "9/10")

    def test_condition_inversion(self):
        row = calculate(PRESETS["rare"])
        self.assertFalse(row["inversion"]["equal"])
        self.assertEqual(row["inversion"]["forward_condition_count"], 10)
        self.assertEqual(row["inversion"]["reverse_condition_count"], 108)

    def test_zero_positive_denominator(self):
        row = calculate(PRESETS["no-positive"])
        self.assertIsNone(row["probabilities"]["ppv"]["fraction"])
        self.assertEqual(row["probabilities"]["ppv"]["denominator"], 0)
        self.assertIsNone(row["bayes"]["posterior"])
        self.assertEqual(row["probabilities"]["sensitivity"]["fraction"], "0")

    def test_absent_class_not_zero_conditional(self):
        row = calculate(PRESETS["no-a"])
        self.assertIsNone(row["probabilities"]["sensitivity"]["fraction"])
        self.assertEqual(row["probabilities"]["ppv"]["fraction"], "0")
        self.assertEqual(row["bayes"]["absent_classes"], ["A"])
        other = calculate(PRESETS["no-b"])
        self.assertIsNone(other["probabilities"]["false_positive_rate"]["fraction"])
        self.assertEqual(other["probabilities"]["ppv"]["fraction"], "1")

    def test_invalid_counts(self):
        for value in (-1, 1.5, True, "9", None, 2001):
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate({**PRESETS["rare"], "ap": value})

    def test_empty_total_and_missing_fields(self):
        for counts in ({"ap":0,"an":0,"bp":0,"bn":0}, {"ap":1}, {**PRESETS["rare"],"extra":1},
                       {"ap":1000,"an":1000,"bp":1000,"bn":1000}, []):
            with self.subTest(counts=counts), self.assertRaises(ValueError):
                calculate(counts)

    def test_small_finite_populations(self):
        # Independent direct fractions for 255 nonempty small 2x2 tables.
        for ap, an, bp, bn in product(range(4), repeat=4):
            if not ap + an + bp + bn:
                continue
            result = calculate(dict(zip(("ap","an","bp","bn"),(ap,an,bp,bn))))
            expected = str(Fraction(ap,ap+bp)) if ap+bp else None
            self.assertEqual(result["bayes"]["posterior"], expected)


if __name__ == "__main__":
    unittest.main()
