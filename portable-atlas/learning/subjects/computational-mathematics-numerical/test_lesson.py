import unittest
from lesson import experiment


class SummationTest(unittest.TestCase):
    def results(self, tokens, order="original"):
        return experiment(tokens, order)["steps"][-1]

    def test_exact_integers(self):
        row = self.results(["1", "2", "3", "4"])
        self.assertEqual(row["oracle_exact"], "10")
        self.assertTrue(all(m["total_error_exact"] == "0" for m in row["methods"].values()))

    def test_kahan_boundary_neumaier_recovers(self):
        row = self.results(["1e16", "1", "-1e16"])
        self.assertEqual(row["methods"]["naive"]["result"], "0.0")
        self.assertEqual(row["methods"]["kahan"]["result"], "0.0")
        self.assertEqual(row["methods"]["neumaier"]["result"], "1.0")
        self.assertEqual(row["methods"]["fsum"]["total_error_exact"], "0")

    def test_kahan_compensation(self):
        row = self.results(["1e16", "1", "1", "-1e16"])
        self.assertEqual(row["methods"]["naive"]["result"], "0.0")
        self.assertEqual(row["methods"]["kahan"]["result"], "2.0")

    def test_order_changes_naive(self):
        tokens = ["1e16", "1", "1", "-1e16"]
        row = self.results(tokens, "small-first")
        self.assertEqual(row["methods"]["naive"]["result"], "2.0")
        self.assertEqual(self.results(tokens)["methods"]["naive"]["result"], "0.0")
        self.assertEqual(row["oracle_exact"], self.results(tokens)["oracle_exact"])

    def test_sorting_does_not_guarantee_recovery(self):
        row = self.results(["1e16", "1", "-1e16"], "small-first")
        self.assertEqual(row["methods"]["naive"]["result"], "0.0")

    def test_input_and_arithmetic_oracles_differ(self):
        row = self.results(["0.1"] * 10)
        self.assertEqual(row["oracle_exact"], "1")
        self.assertNotEqual(row["binary_oracle_exact"], "1")
        self.assertNotEqual(row["conversion_error"], "0")
        self.assertEqual(row["methods"]["fsum"]["total_error_exact"], "0")
        self.assertNotEqual(row["methods"]["fsum"]["arithmetic_error_exact"], "0")

    def test_zero_relative_error_undefined(self):
        self.assertIsNone(self.results(["1", "-1"])["methods"]["naive"]["relative_error"])

    def test_invalid_input_rejected(self):
        for tokens in (["NaN"], ["Infinity"], ["1e309"], ["1e-400"], ["0e99999999"], [], ["1"] * 33, [1], ["bad"]):
            with self.subTest(tokens=tokens), self.assertRaises(ValueError):
                experiment(tokens)

    def test_unknown_order(self):
        with self.assertRaises(ValueError):
            experiment(["1"], "random")


if __name__ == "__main__":
    unittest.main()
