"""Read-only comparisons to independently authored hand-group oracle."""
import sys
sys.dont_write_bytecode = True
from copy import deepcopy
import json
import unittest
from runner import ROOT, MODES, process, run_lesson


class LessonTests(unittest.TestCase):
    def setUp(self):
        self.records = json.loads((ROOT / "fixture.json").read_text())["records"]
        self.oracle = json.loads((ROOT / "hand-groups.json").read_text())

    def test_hand_group_oracle(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                result = process(self.records, mode, 4)
                expected = self.oracle["drop" if mode == "drop" else "generalize"]
                self.assertEqual(result["audit_groups"], expected)
                for field, value in self.oracle["expected_stats"][mode].items():
                    self.assertEqual(result["stats"][field], value)

    def test_output_projection_not_lineage(self):
        for mode in MODES:
            with self.subTest(mode=mode):
                result = process(self.records, mode, 4)
                self.assertEqual(result["release_columns"], self.oracle["release_columns"][mode])
                for row in result["release"]:
                    self.assertEqual(list(row), result["release_columns"])
                    self.assertNotIn("name", row)
                    self.assertNotIn("synthetic_id", row)
                    self.assertNotIn("members", row)

    def test_direct_drop_does_not_remove_uniqueness(self):
        stats = process(self.records, "drop", 2)["stats"]
        self.assertEqual(stats["singleton_source_records"], 12)
        self.assertEqual(stats["min_group_size"], 1)
        self.assertFalse(stats["meets_declared_qi_size_rule"])

    def test_threshold_is_check_not_automatic_transformation(self):
        a, b = process(self.records, "generalize", 4), process(self.records, "generalize", 5)
        self.assertTrue(a["stats"]["meets_declared_qi_size_rule"])
        self.assertFalse(b["stats"]["meets_declared_qi_size_rule"])
        self.assertEqual(a["release"], b["release"])
        self.assertTrue(process(self.records, "drop", 1)["stats"]["meets_declared_qi_size_rule"])

    def test_aggregate_conserves_counts_not_individual_rows(self):
        result = process(self.records, "aggregate", 4)
        self.assertEqual([row["count"] for row in result["release"]], [4, 4, 4])
        self.assertEqual(sum(row["count"] for row in result["release"]), len(self.records))
        self.assertFalse(result["utility"]["row_category_retained"])
        self.assertEqual(result["stats"]["source_records"], 12)
        self.assertEqual(result["stats"]["release_rows"], 3)

    def test_empty_not_vacuous_pass(self):
        for mode in MODES:
            result = process([], mode, 4)
            self.assertEqual(result["release"], [])
            self.assertIsNone(result["stats"]["min_group_size"])
            self.assertIsNone(result["stats"]["meets_declared_qi_size_rule"])
            self.assertEqual(result["stats"]["criterion_status"], "undefined-empty")

    def test_null_rejected_for_every_field(self):
        for field in self.records[0]:
            with self.subTest(field=field):
                rows = deepcopy(self.records)
                rows[0][field] = None
                with self.assertRaises(ValueError):
                    process(rows, "generalize", 4)

    def test_invalid_input_schema_duplicate_and_types(self):
        bad_rows = [None, {}, [None], [{**self.records[0], "extra": "x"}],
                    [{k: v for k, v in self.records[0].items() if k != "age"}],
                    [self.records[0], self.records[0]]]
        for field, value in (("age", True), ("age", -1), ("age", 121), ("age", 24.0), ("age", "24"),
                             ("zone", "A10"), ("zone", ""), ("name", " "), ("category", [])):
            bad_rows.append([{**self.records[0], field: value}])
        for rows in bad_rows:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                process(rows, "drop", 4)

    def test_invalid_k_mode(self):
        for k in (0, -1, None, True, 4.0, "4"):
            with self.subTest(k=k), self.assertRaises(ValueError):
                process(self.records, "drop", k)
        with self.assertRaises(ValueError):
            process(self.records, "unknown", 4)

    def test_generalization_boundaries(self):
        rows = [{**self.records[0], "age": 29}, {**self.records[1], "age": 30}]
        result = process(rows, "generalize", 2)
        self.assertEqual([g["qi"][0] for g in result["audit_groups"]], ["20–29", "30–39"])
        self.assertEqual(result["stats"]["min_group_size"], 1)

    def test_nonmutation_and_determinism(self):
        before = deepcopy(self.records)
        result = process(self.records, "generalize", 4)
        self.assertEqual(self.records, before)
        self.assertEqual(result, process(self.records, "generalize", 4))

    def test_no_privacy_or_dp_credit(self):
        lesson = run_lesson()
        self.assertEqual(len(lesson["runs"]), 9)
        for row in lesson["runs"]:
            self.assertEqual(row["privacy_guarantee"], "not-claimed")
            self.assertFalse(row["differential_privacy"])
        self.assertFalse(lesson["real_reidentification_performed"])


if __name__ == "__main__":
    unittest.main()
