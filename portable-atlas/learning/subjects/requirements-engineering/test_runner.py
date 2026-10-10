"""Read-only by default. --record appends actual finite observations explicitly."""
import sys
sys.dont_write_bytecode = True
import argparse
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import runner
import oracle


class FiniteChecks(unittest.TestCase):
    def run_case(self, case):
        report=runner.observe(case)
        self.assertTrue(report["oracle"]["all_match"])
        self.assertFalse(report["result"]["final_matrix"]["stakeholder_approved"])
        self.assertFalse(report["result"]["final_matrix"]["whole_requirements_complete"])
        return report["result"]

    def test_normal_actual_tests(self):
        r=self.run_case("normal")
        self.assertEqual(r["final_matrix"]["verified"],3)
        self.assertEqual([p["test_id"] for p in r["proofs"]],list(runner.TEST_REQUIREMENTS))
        self.assertEqual(r["proofs"][1]["actual"][-1]["after"],list("ABC"))
        self.assertIs(r["proofs"][1]["actual"][-1]["output"],False)

    def test_boundary_and_empty(self):
        r=self.run_case("boundary")
        self.assertEqual(r["final_matrix"]["verified"],3)
        self.assertEqual(r["proofs"][1]["actual"][-1]["after"],["A"])
        self.assertIsNone(r["proofs"][3]["actual"][0]["output"])

    def test_orphan(self):
        r=self.run_case("orphan")
        self.assertEqual((r["final_matrix"]["verified"],r["final_matrix"]["total"]),(3,4))
        self.assertEqual(r["final_matrix"]["rows"][-1]["status"],"orphan")
        self.assertEqual(r["diff"]["added"][0]["id"],"R-DUP")

    def test_stale_revision(self):
        r=self.run_case("stale-revision")
        self.assertTrue(all(p["passed"] for p in r["proofs"]))
        self.assertEqual(r["final_matrix"]["verified"],0)
        reasons=r["final_matrix"]["rows"][0]["checks"][0]["rejected_evidence"][0]["reasons"]
        self.assertIn("requirement-revision-stale",reasons)
        self.assertIn("app-config-stale",reasons)

    def test_actual_retest_preserves_old_proof(self):
        r=self.run_case("retested-revision")
        self.assertEqual(len(r["proofs"]),8)
        self.assertEqual(r["final_matrix"]["verified"],3)
        changed=next(e for e in r["events"] if e["action"]=="requirements-changed")
        self.assertEqual(changed["matrix"]["verified"],0)
        self.assertEqual(r["proofs"][0]["requirement_revision"],1)
        self.assertEqual(r["proofs"][4]["requirement_revision"],2)

    def test_broken_queue_is_not_coverage(self):
        r=self.run_case("broken-queue")
        self.assertEqual(r["final_matrix"]["verified"],2)
        self.assertEqual(r["final_matrix"]["rows"][0]["status"],"failed")
        self.assertEqual(r["proofs"][1]["actual"][-1]["after"],list("ABCZ"))

    def test_requirement_content_change_without_revision(self):
        r=self.run_case("normal"); reqs=copy.deepcopy(r["plan"]["current_requirements"])
        reqs[0]["statement"]+=" changed"
        m=runner.classify(reqs,r["proofs"],runner.bindings(r["plan"]["current_config"]))
        self.assertEqual(m["rows"][0]["status"],"stale")

    def test_duplicate_and_empty_denominators(self):
        r=self.run_case("normal"); reqs=r["plan"]["current_requirements"]; binding=runner.bindings(r["plan"]["current_config"])
        for rr,pp in [(reqs+[reqs[0]],r["proofs"]),(reqs,r["proofs"]+[r["proofs"][0]])]:
            with self.assertRaises(ValueError): runner.classify(rr,pp,binding)
        missing=copy.deepcopy(reqs); missing[0]["required_tests"]=[]
        with self.assertRaises(ValueError): runner.classify(missing,r["proofs"],binding)

    def test_unmapped_evidence(self):
        r=self.run_case("normal"); p=copy.deepcopy(r["proofs"][0]); p.update(evidence_id="extra",requirement_id="unknown")
        m=runner.classify(r["plan"]["current_requirements"],r["proofs"]+[p],runner.bindings(r["plan"]["current_config"]))
        self.assertEqual(m["unmapped_evidence"],["extra"]); self.assertFalse(m["finite_checks_complete"])

    def test_raw_proof_and_counter_tampering(self):
        r=self.run_case("normal"); binding=runner.bindings(r["plan"]["current_config"])
        changed=copy.deepcopy(r); changed["proofs"][0]["actual"][0]["after"]=["fake"]
        self.assertFalse(oracle.check(changed["plan"],changed,binding)["all_match"])
        changed=copy.deepcopy(r); changed["final_matrix"]["verified"]=99
        self.assertFalse(oracle.check(changed["plan"],changed,binding)["all_match"])
        changed=copy.deepcopy(r); p=changed["proofs"][0]
        p["operations"]=[]; p["actual"]=[]; p["expected"]=[]
        p["evidence_digest"]=runner.sha(runner.canonical({k:v for k,v in p.items() if k!="evidence_digest"}))
        self.assertFalse(oracle.check(changed["plan"],changed,binding)["raw_queue_matches"])

    def test_oracle_does_not_call_app_or_classifier(self):
        r=self.run_case("normal"); binding=runner.bindings(r["plan"]["current_config"])
        with patch.object(runner,"classify",side_effect=AssertionError), patch.object(runner.QueueApp,"enqueue",side_effect=AssertionError):
            self.assertTrue(oracle.check(r["plan"],r,binding)["all_match"])

    def test_declared_finite_input(self):
        with self.assertRaises(ValueError): runner.fixture("unknown")
        with self.assertRaises(ValueError): runner.test_plan("T-FAKE",3)
        for capacity in (0,4,True):
            with self.assertRaises(ValueError): runner.QueueApp(capacity)
        for case in runner.CASES:
            r=self.run_case(case)
            self.assertLessEqual(len(r["events"]),11)
            self.assertTrue(all(len(p["actual"])<=6 for p in r["proofs"]))

    def test_failed_publish_retains_prior(self):
        with tempfile.TemporaryDirectory(prefix="requirements-durability-") as directory:
            root=Path(directory); report=runner.observe("normal")
            prior=runner.publish(report,"checks",root)
            before={p.name:runner.sha(p.read_bytes()) for p in prior.iterdir()}
            with self.assertRaises(OSError): runner.publish(report,"checks",root,fail_before_publish=True)
            self.assertEqual(before,{p.name:runner.sha(p.read_bytes()) for p in prior.iterdir()})
            self.assertEqual(len(list(root.glob("checks-*"))),1)


if __name__=="__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--record",action="store_true"); args=parser.parse_args()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(FiniteChecks)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): raise SystemExit(1)
    if args.record:
        for case in runner.CASES:
            report=runner.observe(case,["python3","-B","test_runner.py","--record"])
            print(runner.publish(report,"checks-"+case).relative_to(runner.ROOT))
