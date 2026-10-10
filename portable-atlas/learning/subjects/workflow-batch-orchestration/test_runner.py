"""Default checks do not write artifacts. --record additionally exercises durability."""
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
from runner import ROOT, canonical, fixture, independent_oracle, observe, publish, run, topology


class DAGTest(unittest.TestCase):
    def test_normal_dependency_order_and_values(self):
        result = run(fixture())
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual(result["order"], ["A", "B", "C", "D"])
        self.assertEqual([result["tasks"][n]["value"] for n in result["order"]], [2, 4, 5, 9])
        for event in result["events"]:
            if event["action"] == "started":
                self.assertTrue(all(event["state"][d]["state"] == "succeeded" for d in result["plan"]["tasks"][event["task"]]["deps"]))

    def test_permutation_oracle_is_independent(self):
        plan = fixture()
        with patch("runner.topology", side_effect=AssertionError("oracle must not use topology")), patch("runner.invoke", side_effect=AssertionError("oracle must not invoke tasks")):
            oracle = independent_oracle(plan)
        self.assertEqual(oracle["permutations_examined"], 24)
        self.assertEqual(oracle["valid_orders"], [["A", "B", "C", "D"], ["A", "C", "B", "D"]])
        self.assertEqual(oracle["expected"]["D"]["value"], 9)

    def test_failure_blocks_downstream_not_sibling(self):
        result = run(fixture("always-fail", 1))
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["tasks"]["B"]["attempts"], 2)
        self.assertEqual(result["tasks"]["C"]["state"], "succeeded")
        self.assertEqual(result["tasks"]["D"]["state"], "blocked")
        self.assertFalse(any(x["task"] == "D" for x in result["invocations"]))

    def test_retry_once_recovers_and_zero_retry_fails(self):
        for retries in (0, 1, 2):
            result = run(fixture("fail-once", retries))
            self.assertEqual(result["tasks"]["B"]["attempts"], 1 if retries == 0 else 2)
            self.assertEqual(result["status"], "failed" if retries == 0 else "succeeded")
            failures = [e for e in result["events"] if e["action"] == "attempt-failed"]
            self.assertEqual(len(failures), 1)
            self.assertEqual(failures[0]["state"]["B"]["state"], "failed" if retries == 0 else "retrying")

    def test_retry_upper_bound_not_unlimited(self):
        for retries in (0, 1, 2):
            result = run(fixture("always-fail", retries))
            self.assertEqual(result["tasks"]["B"]["attempts"], retries + 1)
            self.assertEqual(result["tasks"]["B"]["state"], "failed")
            self.assertEqual(result["tasks"]["D"]["attempts"], 0)

    def test_cycle_and_self_cycle_rejected_before_invocation(self):
        for plan in (fixture("cycle"), {"seed": 2, "retries": 1, "tasks": {"A": {"deps": ["A"], "op": "sum", "fail_first": 0}}}):
            with patch("runner.invoke", side_effect=AssertionError("must not start a task")):
                result = run(plan)
            self.assertEqual(result["status"], "rejected")
            self.assertEqual(result["invocations"], [])
            self.assertTrue(independent_oracle(plan)["cycle"])

    def test_reuse_successes_without_reinvoking_or_mutating_prior(self):
        previous = run(fixture("fail-once"))
        before = canonical(previous)
        with patch("runner.invoke", side_effect=AssertionError("all successes reused")):
            result = run(fixture("fail-once"), previous)
        self.assertEqual(canonical(previous), before)
        self.assertEqual(result["invocations"], [])
        self.assertTrue(all(t["reused"] and t["attempts"] == 0 for t in result["tasks"].values()))
        self.assertTrue(observe("fail-once", previous=previous)["oracle_matches"])

    def test_reuse_failure_remains_bounded_fresh_run_duplicates_pure_work(self):
        plan = fixture("always-fail", 1)
        previous = run(plan)
        result = run(plan, previous)
        self.assertEqual([x["task"] for x in result["invocations"]], ["B", "B"])
        self.assertTrue(result["tasks"]["A"]["reused"] and result["tasks"]["C"]["reused"])
        self.assertEqual(result["tasks"]["D"]["state"], "blocked")
        self.assertEqual(canonical(run(plan)), canonical(previous))
        normal = fixture()
        self.assertEqual(len(run(normal)["invocations"]), 4)
        self.assertEqual(len(run(normal)["invocations"]), 4)  # new run means fresh computation, not exactly-once

    def test_resume_refuses_changed_input_source_or_tampered_output(self):
        previous = run(fixture())
        bad_source = copy.deepcopy(previous)
        bad_source["source_digest"] = "0" * 64
        bad_value = copy.deepcopy(previous)
        bad_value["tasks"]["B"]["value"] = 99
        bad_attempt = copy.deepcopy(previous)
        bad_attempt["tasks"]["A"]["attempts"] = 99
        for plan, prior in ((fixture(seed=3), previous), (fixture(retries=2), previous), (fixture(), bad_source), (fixture(), bad_value), (fixture(), bad_attempt)):
            with self.assertRaises(ValueError):
                run(plan, prior)

    def test_invalid_input_is_not_repaired_or_executed(self):
        for case, retries, seed in (("unknown", 1, 2), ("normal", True, 2), ("normal", 3, 2), ("normal", 1, 0)):
            with self.assertRaises(ValueError):
                fixture(case, retries, seed)
        bad = fixture()
        bad["tasks"]["D"]["deps"] = ["Z"]
        duplicate = fixture()
        duplicate["tasks"]["D"]["deps"] = ["B", "B"]
        unknown_op = fixture()
        unknown_op["tasks"]["A"]["op"] = "shell-command"
        for plan in (bad, duplicate, unknown_op):
            with patch("runner.invoke", side_effect=AssertionError("invalid must not execute")), self.assertRaises(ValueError):
                run(plan)

    def test_matrix_seed_case_retry_all_match_oracle(self):
        for seed in (1, 2, 9):
            for case in ("normal", "fail-once", "always-fail", "cycle"):
                for retries in (0, 1, 2):
                    self.assertTrue(observe(case, retries, seed)["oracle_matches"])

    def test_deterministic_raw_trace_and_inputs_immutable(self):
        plan = fixture("fail-once")
        before = canonical(plan)
        self.assertEqual(run(plan), run(plan))
        self.assertEqual(canonical(plan), before)
        self.assertFalse(observe()["execution"]["external_side_effects"])


def record_checks(output, result):
    # Explicit record mode alone writes temporary durability trials and durable check artifacts.
    with tempfile.TemporaryDirectory(prefix=".staging-durability-", dir=ROOT) as scratch:
        root = Path(scratch)
        payload = observe("normal")
        first = publish(payload, root=root)
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first.iterdir()}
        try:
            publish(observe("always-fail"), root=root, fail_before_publish=True)
        except OSError:
            pass
        else:
            raise AssertionError("staging failure expected")
        assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first.iterdir()}
        second = publish(observe("fail-once"), root=root)
        assert first != second and first.is_dir() and second.is_dir()
        metadata = json.loads((second / "metadata.json").read_text())
        assert metadata["sha256"] == hashlib.sha256((second / "result.json").read_bytes()).hexdigest()
    payload = observe(command=["python3", "-B", "test_runner.py", "--record"])
    payload["matrix_observations"] = [observe(case, retries, seed, command=["test_runner.py --record", "matrix"])
                                      for seed in (1, 2, 9) for case in ("normal", "fail-once", "always-fail", "cycle")
                                      for retries in (0, 1, 2)]
    payload["checks"] = {"tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                         "skipped": len(result.skipped), "successful": result.wasSuccessful(),
                         "durability": {"injected_staging_failure": True, "previous_digest_preserved": True,
                                        "append_unique_run": True, "artifact_hash_verified": True}, "stdout_stderr": output}
    location = publish(payload, "checks")
    print("record: " + str(location.relative_to(ROOT)), file=sys.stderr)


if __name__ == "__main__":
    record = "--record" in sys.argv
    buffer = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DAGTest)
    result = unittest.TextTestRunner(stream=buffer, verbosity=2).run(suite)
    print(buffer.getvalue(), file=sys.stderr)
    if record:
        record_checks(buffer.getvalue(), result)
    raise SystemExit(0 if result.wasSuccessful() else 1)
