"""Read-only default. --record explicitly appends raw checks and durability trial."""
import sys
sys.dont_write_bytecode = True
import copy
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from runner import ROOT, CASES, ImmutableStore, artifact, canonical, fixture, inspect_artifact, observe, publish, simulate
from oracle import check


class ReleaseTest(unittest.TestCase):
    def test_normal_digest_binding_and_rollback(self):
        r = simulate(fixture())
        p = next(e for e in r["events"] if e["stage"] == "promotion")
        self.assertEqual(p["active"], r["events"][1]["test"]["artifact_digest"])
        self.assertTrue(all(p["guards"].values()))
        self.assertEqual(r["summary"]["active"], r["summary"]["original_active"])
        self.assertTrue(r["summary"]["previous_bytes_unchanged"])
        self.assertEqual(len(r["final"]["objects"]), 2)

    def test_test_to_candidate_swap_refused(self):
        r = simulate(fixture("test-swap"))
        self.assertFalse(r["summary"]["candidate_accepted"])
        self.assertFalse(r["summary"]["promoted"])
        self.assertEqual(r["events"][-2]["reason"], "test-artifact-mismatch")
        self.assertEqual(r["summary"]["active"], r["summary"]["original_active"])

    def test_candidate_to_promotion_swap_refused(self):
        r = simulate(fixture("promotion-swap"))
        self.assertTrue(r["summary"]["candidate_accepted"])
        self.assertFalse(r["summary"]["promoted"])
        self.assertFalse(r["events"][-2]["guards"]["workspace_matches"])
        self.assertEqual(r["summary"]["active"], r["summary"]["original_active"])

    def test_failed_check_blocks_candidate(self):
        r = simulate(fixture("failed-test"))
        self.assertFalse(r["events"][1]["test"]["checks"]["ready"])
        self.assertEqual(r["events"][-2]["reason"], "failed-test")
        self.assertFalse(r["summary"]["promoted"])

    def test_missing_history_refuses_rollback_without_fallback(self):
        r = simulate(fixture("missing-history"))
        self.assertTrue(r["summary"]["promoted"])
        self.assertEqual(r["final"]["reason"], "missing-history; no fallback build or invented previous release")
        self.assertEqual(r["summary"]["rollback_status"], "refused")
        self.assertIsNone(r["summary"]["original_active"])
        self.assertEqual(len(r["final"]["objects"]), 1)

    def test_no_rollback_is_distinct_from_refusal(self):
        r = simulate(fixture("normal", False))
        self.assertEqual(r["summary"]["rollback_status"], "not-requested")
        self.assertNotEqual(r["summary"]["active"], r["summary"]["original_active"])

    def test_immutable_store_snapshot_cannot_change_bytes(self):
        store = ImmutableStore(); blob=artifact(1); key=store.put(blob)
        store.snapshot()[key]["hex"] = artifact(3).hex()
        self.assertEqual(store.get(key), blob)
        self.assertEqual(store.put(blob), key)
        with self.assertRaises(ValueError): store.put(bytearray(blob))

    def test_real_bytes_check_and_invalid_inputs(self):
        for blob in (b"", b"bad", b"prefix\x00{}", artifact(4), artifact(2, False)):
            self.assertFalse(inspect_artifact(blob)["passed"])
        for case, rollback in (("unknown",True),("normal",1),("normal",None)):
            with self.assertRaises(ValueError): fixture(case, rollback)
        bad=fixture(); bad["build_hex"]=b"bad".hex()
        with self.assertRaises(ValueError): simulate(bad)

    def test_independent_oracle_tamper_detection(self):
        plan=fixture(); r=simulate(plan)
        with patch("runner.simulate",side_effect=AssertionError("independent")):
            self.assertTrue(check(plan,r)["all_match"])
        for path in ("active", "working_digest"):
            bad=copy.deepcopy(r); bad["events"][3][path]="0"*64
            self.assertFalse(check(plan,bad)["all_match"])
        bad=copy.deepcopy(r); bad["events"][3]["guards"]["test_record_matches"]=False
        self.assertFalse(check(plan,bad)["all_match"])
        bad=copy.deepcopy(r); bad["events"][1]["test"]["artifact_digest"]="0"*64
        self.assertFalse(check(plan,bad)["all_match"])
        bad=copy.deepcopy(r); bad["events"][-1]["guards"]["stored_bytes_match"]=False
        self.assertFalse(check(plan,bad)["all_match"])
        bad=copy.deepcopy(r); bad["plan_digest"]="0"*64
        self.assertFalse(check(plan,bad)["all_match"])
        bad=copy.deepcopy(r); bad["events"][1]["seq"]=5
        self.assertFalse(check(plan,bad)["all_match"])

    def test_all_cases_and_determinism(self):
        for case in CASES:
            for rollback in (False,True):
                plan=fixture(case,rollback); before=canonical(plan)
                r=simulate(plan)
                self.assertTrue(check(plan,r)["all_match"])
                self.assertEqual(r,simulate(plan)); self.assertEqual(before,canonical(plan))
                self.assertLessEqual(len(r["events"]),6)
                self.assertFalse(observe(case,rollback)["execution"]["deployed"])


def record_checks(output, result):
    with tempfile.TemporaryDirectory(prefix=".staging-durability-",dir=ROOT) as scratch:
        first=publish(observe(),root=Path(scratch))
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in first.iterdir()}
        error=None
        try: publish(observe("failed-test"),root=Path(scratch),fail_before_publish=True)
        except OSError as exc: error=str(exc)
        after={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in first.iterdir()}
        assert error and before==after
        second=publish(observe("test-swap"),root=Path(scratch))
        assert second!=first
    payload=observe(command=["python3","-B","test_runner.py","--record"])
    payload["checks"]={"tests_run":result.testsRun,"successful":result.wasSuccessful(),"failures":len(result.failures),
                       "errors":len(result.errors),"skipped":len(result.skipped),"output":output,
                       "durability":{"intentional_error":error,"prior_before":before,"prior_after":after,"prior_unchanged":before==after,"unique_append":True}}
    payload["matrix_observations"]=[observe(c,r,command=["test_runner.py --record","matrix"]) for c in CASES for r in (False,True)]
    print("record: "+str(publish(payload,"checks").relative_to(ROOT)),file=sys.stderr)


if __name__ == "__main__":
    output=io.StringIO()
    result=unittest.TextTestRunner(stream=output,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ReleaseTest))
    print(output.getvalue(),file=sys.stderr)
    if "--record" in sys.argv: record_checks(output.getvalue(),result)
    raise SystemExit(0 if result.wasSuccessful() else 1)
