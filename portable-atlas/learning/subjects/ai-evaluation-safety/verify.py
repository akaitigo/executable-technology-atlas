#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Check independent hand counts, threshold boundaries and invalid inputs."""
import copy
import json
import math
import unittest

from evaluate import ROOT, evaluate, observation


class MetricTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.samples = json.loads((ROOT / "predictions.json").read_text())["samples"]
        cls.oracle = json.loads((ROOT / "hand-count.json").read_text())

    def test_independent_hand_count_oracle(self):
        for case in self.oracle["cases"]:
            with self.subTest(threshold=case["threshold"]):
                actual = evaluate(self.samples, case["threshold"])
                self.assertEqual(actual["counts"], case["counts"])
                for outcome, ids in case["groups"].items():
                    self.assertEqual([r["id"] for r in actual["decisions"] if r["outcome"] == outcome], ids)
                    self.assertEqual(case["counts"][outcome], len(ids))
                for name, expected in case["metrics"].items():
                    metric = actual["metrics"][name]
                    if expected is None:
                        self.assertIsNone(metric["value"])
                        self.assertEqual(metric["status"], "undefined-zero-denominator")
                    else:
                        self.assertAlmostEqual(metric["value"], expected)

    def test_same_accuracy_can_hide_all_positive_misses(self):
        low, medium, _, high = observation()["results"]
        self.assertEqual([r["metrics"]["accuracy"]["value"] for r in (low, medium, high)], [0.9, 0.9, 0.9])
        self.assertEqual([r["counts"]["FN"] for r in (low, medium, high)], [0, 1, 2])
        self.assertEqual([r["counts"]["FP"] for r in (low, medium, high)], [2, 1, 0])

    def test_equal_to_threshold_is_positive(self):
        row = evaluate([{"id": "boundary", "label": 1, "score": 0.8}], 0.8)
        self.assertEqual(row["counts"]["TP"], 1)

    def test_zero_denominators_are_explicit(self):
        negative = evaluate([{"id": "n", "label": 0, "score": 0}], 1)
        self.assertIsNone(negative["metrics"]["precision"]["value"])
        self.assertIsNone(negative["metrics"]["recall"]["value"])
        self.assertEqual(negative["metrics"]["fpr"]["value"], 0)
        positive = evaluate([{"id": "p", "label": 1, "score": 1}], 0)
        self.assertIsNone(positive["metrics"]["fpr"]["value"])
        self.assertEqual(positive["metrics"]["precision"]["value"], 1)

    def test_empty_dataset_is_rejected(self):
        for invalid in ([], None, {}, "samples"):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "nonempty list"):
                    evaluate(invalid, 0.5)

    def test_invalid_thresholds_are_rejected(self):
        for invalid in (-0.01, 1.01, math.nan, math.inf, -math.inf, True, "0.5", None):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "threshold"):
                    evaluate(self.samples, invalid)

    def test_invalid_scores_and_labels_are_rejected(self):
        for field, invalid in [("score", math.nan), ("score", math.inf), ("score", -0.01), ("score", 1.01), ("score", True), ("score", "0.8"), ("label", True), ("label", 2), ("label", 0.0), ("label", "1")]:
            candidate = copy.deepcopy(self.samples)
            candidate[0][field] = invalid
            with self.subTest(field=field, invalid=invalid):
                with self.assertRaises(ValueError):
                    evaluate(candidate, 0.5)

    def test_duplicate_missing_and_extra_fields_are_rejected(self):
        duplicate = copy.deepcopy(self.samples)
        duplicate[1]["id"] = duplicate[0]["id"]
        missing = copy.deepcopy(self.samples)
        missing[0].pop("score")
        extra = copy.deepcopy(self.samples)
        extra[0]["prediction"] = 1
        malformed = copy.deepcopy(self.samples)
        malformed[0] = None
        for candidate in (duplicate, missing, extra, malformed):
            with self.assertRaises(ValueError):
                evaluate(candidate, 0.5)

    def test_input_is_not_mutated(self):
        before = copy.deepcopy(self.samples)
        evaluate(self.samples, 0.5)
        self.assertEqual(self.samples, before)


if __name__ == "__main__":
    unittest.main()
