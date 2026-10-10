"""Read-only checks by default. --record explicitly writes raw checks/matrix/durability."""
import sys
sys.dont_write_bytecode = True
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from runner import ROOT, canonical, fixture, observe, publish, simulate
from oracle import check, small_feasibility, unit_timeline


class EDFTest(unittest.TestCase):
    def test_normal_feasible_and_preemption(self):
        result = simulate(fixture())
        self.assertEqual(result["summary"]["misses"], 0)
        self.assertFalse(result["summary"]["safe_state"])
        self.assertEqual(result["summary"]["utilization"], .75)
        self.assertTrue(any(e["action"] == "preempted" and e["time"] == 8 and e["job"] == "B1" for e in result["events"]))
        self.assertTrue(small_feasibility(fixture())["feasible_schedule_exists"])

    def test_exact_deadline_finish_is_not_a_miss(self):
        result = simulate(fixture("boundary"))
        self.assertEqual(result["summary"]["utilization"], 1.0)
        self.assertEqual(result["summary"]["misses"], 0)
        exact = [j for j in result["jobs"].values() if j["finish"] == j["deadline"]]
        self.assertTrue(exact)
        self.assertTrue(all(j["lateness"] == 0 and j["tardiness"] == 0 and not j["missed"] for j in exact))
        self.assertTrue(small_feasibility(fixture("boundary"))["feasible_schedule_exists"])

    def test_overload_miss_lateness_and_flag(self):
        result = simulate(fixture("overload"))
        self.assertEqual(result["summary"]["utilization"], 1.25)
        self.assertEqual(result["summary"]["safe_since"], 8)
        self.assertEqual(result["jobs"]["A1"]["finish"], 9)
        self.assertEqual(result["jobs"]["A1"]["lateness"], 1)
        self.assertEqual(result["jobs"]["A1"]["tardiness"], 1)
        self.assertFalse(small_feasibility(fixture("overload"))["feasible_schedule_exists"])

    def test_flag_is_latched_but_not_a_safety_device_or_cpu_stop(self):
        result = simulate(fixture("overload", 24))
        latch = [e for e in result["events"] if e["action"] == "safe-state-latched"]
        self.assertEqual(len(latch), 1)
        self.assertTrue(all(e["safe_state"] for e in result["events"] if e["seq"] >= latch[0]["seq"]))
        self.assertTrue(any(s["start"] >= 8 for s in result["segments"]))
        self.assertFalse(observe("overload")["execution"]["safety_device"])

    def test_release_deadline_finish_ledger_and_cpu_conservation(self):
        for case in ("normal", "boundary", "overload"):
            result = simulate(fixture(case, 24))
            self.assertEqual(sum(s["end"] - s["start"] for s in result["segments"]), 24)
            self.assertEqual(result["segments"][0]["start"], 0)
            self.assertTrue(all(a["end"] == b["start"] for a, b in zip(result["segments"], result["segments"][1:])))
            for jid, item in result["jobs"].items():
                used = sum(s["end"] - s["start"] for s in result["segments"] if s["job"] == jid)
                self.assertEqual(used + item["remaining"], item["execution"])
                self.assertTrue(all(s["start"] >= item["release"] for s in result["segments"] if s["job"] == jid))
                checks = [e for e in result["events"] if e["job"] == jid and e["action"] in ("deadline-miss", "deadline-met")]
                self.assertEqual(len(checks), 1 if item["deadline"] <= 24 else 0)

    def test_oracle_does_not_call_runner_and_detects_tampering(self):
        plan = fixture("overload")
        result = simulate(plan)
        with patch("runner.simulate", side_effect=AssertionError("oracle independence")):
            self.assertTrue(check(plan, result)["all_match"])
        bad = copy.deepcopy(result)
        bad["segments"][0]["job"] = "B0"
        self.assertFalse(check(plan, bad)["timeline_matches"])
        bad = copy.deepcopy(result)
        bad["jobs"]["A1"]["missed"] = False
        self.assertFalse(check(plan, bad)["jobs_match"])
        bad = copy.deepcopy(result)
        bad["summary"]["safe_state"] = False
        self.assertFalse(check(plan, bad)["safe_flag_matches"])

    def test_matrix_and_trace_bounds(self):
        for case in ("normal", "boundary", "overload"):
            for horizon in (12, 24, 36):
                report = observe(case, horizon)
                self.assertTrue(report["oracle"]["all_match"])
                self.assertLessEqual(len(report["result"]["events"]), 200)
                self.assertTrue(all(e["time"] <= horizon for e in report["result"]["events"]))

    def test_horizon_truncation_not_a_false_finish_or_release(self):
        plan = fixture("overload", 5)
        result = simulate(plan)
        self.assertTrue(check(plan, result)["all_match"])
        self.assertGreater(result["summary"]["unfinished"], 0)
        self.assertTrue(all(j["release"] < 5 for j in result["jobs"].values()))
        self.assertTrue(any(j["finish"] is None and j["deadline"] > 5 and not j["missed"] for j in result["jobs"].values()))
        at12 = simulate(fixture("normal", 12))
        self.assertNotIn("A3", at12["jobs"])
        self.assertNotIn("B2", at12["jobs"])

    def test_invalid_inputs_refused(self):
        for case, horizon in (("unknown", 12), ("normal", True), ("normal", 0), ("normal", 37), ("normal", 12.0)):
            with self.assertRaises(ValueError):
                fixture(case, horizon)
        for field, value in (("period", 0), ("execution", 0), ("execution", 9), ("period", True)):
            bad = fixture()
            bad["tasks"]["A"][field] = value
            with self.assertRaises(ValueError):
                simulate(bad)

    def test_deterministic_and_input_unchanged(self):
        plan = fixture("overload", 24)
        before = canonical(plan)
        self.assertEqual(simulate(plan), simulate(plan))
        self.assertEqual(before, canonical(plan))
        self.assertFalse(observe()["execution"]["real_os_realtime"])


def record_checks(output, result):
    with tempfile.TemporaryDirectory(prefix=".staging-durability-", dir=ROOT) as scratch:
        root = Path(scratch)
        first = publish(observe(), root=root)
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first.iterdir()}
        error = None
        try:
            publish(observe("overload"), root=root, fail_before_publish=True)
        except OSError as exc:
            error = str(exc)
        assert error is not None
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first.iterdir()}
        assert before == after
        second = publish(observe("boundary"), root=root)
        assert second != first
    payload = observe(command=["python3", "-B", "test_runner.py", "--record"])
    payload["checks"] = {"tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                         "skipped": len(result.skipped), "successful": result.wasSuccessful(), "output": output,
                         "durability": {"intentional_error": error, "prior_before": before, "prior_after": after,
                                        "prior_unchanged": before == after, "unique_append": True}}
    payload["matrix_observations"] = [observe(case, horizon, command=["test_runner.py --record", "matrix"])
                                      for case in ("normal", "boundary", "overload") for horizon in (12, 24, 36)]
    location = publish(payload, "checks")
    print("record: " + str(location.relative_to(ROOT)), file=sys.stderr)


if __name__ == "__main__":
    buffer = io.StringIO()
    result = unittest.TextTestRunner(stream=buffer, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(EDFTest))
    print(buffer.getvalue(), file=sys.stderr)
    if "--record" in sys.argv:
        record_checks(buffer.getvalue(), result)
    raise SystemExit(0 if result.wasSuccessful() else 1)
