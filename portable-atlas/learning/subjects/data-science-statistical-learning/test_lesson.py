import copy
from fractions import Fraction
import itertools
import unittest
from lesson import PRESETS, OOD, calculate, fit_ols, invalid_inputs
from oracle import solve, score


class OLSTest(unittest.TestCase):
    def test_literal_normal_coefficients_and_mse(self):
        models = calculate(PRESETS["train-only"])["models"]
        normal = models["train-only"]
        self.assertEqual(normal["exact_oracle"]["intercept"], "1")
        self.assertEqual(normal["exact_oracle"]["slope"], "9/5")
        self.assertEqual(normal["exact_oracle"]["mse"], {"train": "8/25", "holdout": "108/25", "ood": "24212/75"})
        self.assertAlmostEqual(normal["intercept"], 1)
        self.assertAlmostEqual(normal["slope"], 1.8)

    def test_fit_leakage_changes_fit_members_and_coefficients(self):
        result = calculate(PRESETS["fit-leakage"])
        leaky = result["models"]["fit-leakage"]
        self.assertEqual(leaky["exact_oracle"]["intercept"], "2")
        self.assertEqual(leaky["exact_oracle"]["mse"]["train"], "33/25")
        self.assertEqual(leaky["exact_oracle"]["mse"]["holdout"], "33/25")
        self.assertEqual(len(leaky["fit_row_ids"]), 10)
        self.assertFalse(leaky["holdout_independent"])

    def test_selection_leakage_is_not_independent_test(self):
        result = calculate(PRESETS["selection-leakage"])
        leaky = result["models"]["selection-leakage"]
        self.assertEqual(leaky["selected_offset"], 2)
        self.assertEqual(leaky["exact_oracle"]["intercept"], "3")
        self.assertEqual(leaky["exact_oracle"]["mse"]["train"], "108/25")
        self.assertEqual(leaky["exact_oracle"]["mse"]["holdout"], "8/25")
        self.assertEqual(leaky["exact_oracle"]["mse"]["ood"], "6504/25")
        self.assertEqual(len(leaky["fit_row_ids"]), 5)
        self.assertEqual(len(leaky["selection_row_ids"]), 5)
        self.assertFalse(leaky["holdout_independent"])

    def test_train_only_fit_is_invariant_to_holdout_labels(self):
        original = calculate(PRESETS["train-only"])["models"]["train-only"]
        changed = copy.deepcopy(PRESETS["train-only"])
        changed["holdout"] = [[x, y + 10] for x, y in changed["holdout"]]
        altered = calculate(changed)["models"]["train-only"]
        for field in ("intercept", "slope", "fit_row_ids", "selection_row_ids"):
            self.assertEqual(original[field], altered[field])
        self.assertNotEqual(original["evaluations"]["holdout"]["mse"], altered["evaluations"]["holdout"]["mse"])
        self.assertTrue(altered["holdout_independent"])

    def test_closed_form_oracle_on_many_small_datasets(self):
        for ys in itertools.product(range(-2, 3), repeat=3):
            points = list(map(list, zip((-1, 0, 1), ys)))
            a, b = solve(points)
            fitted = fit_ols(points)
            self.assertAlmostEqual(fitted["intercept"], float(a))
            self.assertAlmostEqual(fitted["slope"], float(b))
            residuals = [Fraction(y) - a - b * x for x, y in points]
            self.assertEqual(sum(residuals), 0)
            self.assertEqual(sum(x * r for (x, _), r in zip(points, residuals)), 0)
            optimum = score(points, (a, b))
            self.assertGreater(score(points, (a + 1, b)), optimum)
            self.assertGreater(score(points, (a, b + 1)), optimum)

    def test_order_and_affine_response(self):
        points = PRESETS["train-only"]["train"]
        base = fit_ols(points)
        for permuted in itertools.permutations(points):
            self.assertAlmostEqual(fit_ols(permuted)["slope"], base["slope"])
        transformed = fit_ols([[x, y * 3 + 7] for x, y in points])
        self.assertAlmostEqual(transformed["intercept"], 3 * base["intercept"] + 7)
        self.assertAlmostEqual(transformed["slope"], 3 * base["slope"])

    def test_exact_line_and_minimum_two_points(self):
        for name in ("exact-line", "two-points"):
            result = calculate(PRESETS[name])["models"]["train-only"]
            self.assertEqual(result["exact_oracle"]["intercept"], "1")
            self.assertEqual(result["exact_oracle"]["slope"], "2")
            self.assertEqual(result["exact_oracle"]["mse"]["train"], "0")

    def test_invalid_empty_constant_and_unsupported(self):
        for data in invalid_inputs():
            with self.subTest(data=data), self.assertRaises(ValueError):
                calculate(data)
        for points in ([], [[1, 2], [1, 3]]):
            with self.assertRaises(ValueError):
                fit_ols(points)

    def test_rejection_then_recovery_and_duplicate_x(self):
        with self.assertRaises(ValueError):
            calculate({**PRESETS["train-only"], "train": [[1, 2], [1, 3]]})
        valid = {**PRESETS["train-only"], "train": [[0, 1], [0, 2], [1, 3]], "holdout": [[1, 3]]}
        self.assertTrue(calculate(valid)["models"]["train-only"]["holdout_independent"])

    def test_ood_never_fits_or_selects(self):
        for mode in ("train-only", "fit-leakage", "selection-leakage"):
            result = calculate(PRESETS[mode])
            self.assertEqual(result["ood"], OOD)
            for model in result["models"].values():
                self.assertFalse(model["ood_used_for_fit_or_selection"])
                self.assertFalse(any(row.startswith("ood.") for row in model["fit_row_ids"] + model["selection_row_ids"]))


if __name__ == "__main__":
    unittest.main()
