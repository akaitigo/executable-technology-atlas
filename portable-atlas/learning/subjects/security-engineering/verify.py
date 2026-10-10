"""Read-only checks against original independent permission matrix."""
import sys
sys.dont_write_bytecode = True
from copy import deepcopy
import json
import unittest
from runner import ROOT, controlled, fixture, lookup_only, run_lesson


class LessonTests(unittest.TestCase):
    def setUp(self):
        self.data = fixture()
        self.oracle = json.loads((ROOT / "oracle.json").read_text())

    def test_independent_matrix_all_cells(self):
        run = run_lesson()["matrix_runs"]
        actual = {r["id"]: r for r in run}
        expected = {f'{r["actor"]}/{r["resource"]}/{r["operation"]}': r for r in self.oracle["matrix"]}
        self.assertEqual(len(actual), 16)
        self.assertEqual(set(actual), set(expected))
        for case_id, e in expected.items():
            with self.subTest(case=case_id):
                response = actual[case_id]["controlled"]
                self.assertEqual(response["response"]["status"], e["status"])
                self.assertEqual(response["decision"]["reason"], e["reason"])
                if e["status"] == 200:
                    self.assertEqual(response["response"]["body"]["payload"], self.oracle["allowed_payloads"][e["resource"]])
                else:
                    self.assertEqual(response["response"]["body"], {"error": "forbidden"})

    def test_bug_is_observed_not_silently_fixed(self):
        rows = run_lesson()["matrix_runs"]
        self.assertEqual(sum(r["lookup_only"]["response"]["status"] == 200 for r in rows), 16)
        self.assertEqual(sum(r["controlled"]["response"]["status"] == 200 for r in rows), 3)
        leak = next(r for r in rows if r["id"] == "actor-a/blue-report/read")
        self.assertEqual(leak["lookup_only"]["response"]["body"]["payload"], "FICTIONAL BLUE REPORT")
        self.assertEqual(leak["controlled"]["response"], {"status": 403, "body": {"error": "forbidden"}})

    def test_independent_boundary_oracle(self):
        rows = run_lesson()["boundary_runs"]
        self.assertEqual({r["id"] for r in rows}, set(self.oracle["boundary_expected"]))
        for row in rows:
            with self.subTest(case=row["id"]):
                expected = self.oracle["boundary_expected"][row["id"]]
                for name in ("lookup_only", "controlled"):
                    self.assertEqual(row[name]["response"]["status"], expected["status"])
                    self.assertEqual(row[name]["decision"]["reason"], expected["reason"])
                    self.assertNotIn("payload", row[name]["response"]["body"])

    def test_tenant_not_bypassed_even_with_extra_grant(self):
        self.data["actors"]["actor-a"]["grants"].append({"operation":"read","resource_id":"blue-report","resource_type":"report"})
        result = controlled({"actor_id":"actor-a"}, {"object_id":"blue-report","operation":"read"}, self.data)
        self.assertEqual(result["decision"]["reason"], "tenant-mismatch")

    def test_operation_and_resource_type_binding(self):
        context = {"actor_id":"actor-a"}
        self.assertEqual(controlled(context, {"object_id":"red-report","operation":"export"}, self.data)["decision"]["reason"], "no-grant")
        self.data["records"]["red-report"]["resource_type"] = "archive"
        self.assertEqual(controlled(context, {"object_id":"red-report","operation":"read"}, self.data)["decision"]["reason"], "no-grant")

    def test_same_tenant_is_not_all_resource_access(self):
        result = controlled({"actor_id":"actor-a"}, {"object_id":"red-archive","operation":"read"}, self.data)
        self.assertEqual(result["decision"]["reason"], "no-grant")

    def test_request_types_empty_extra_fields(self):
        context = {"actor_id":"actor-a"}
        for request in (None, [], {}, {"object_id":"","operation":"read"},
                        {"object_id":True,"operation":"read"}, {"object_id":[],"operation":"read"},
                        {"object_id":"red-report","operation":""}, {"object_id":"red-report","operation":"read","actor_id":"actor-b"}):
            with self.subTest(request=request):
                self.assertEqual(controlled(context, request, self.data)["response"]["status"], 400)

    def test_context_types_and_null(self):
        request = {"object_id":"red-report","operation":"read"}
        for context in ([], {}, {"actor_id":True}, {"actor_id":""}, {"actor_id":"actor-a","tenant":"tenant-blue"}):
            with self.subTest(context=context):
                self.assertEqual(controlled(context, request, self.data)["response"]["status"], 400)
        self.assertEqual(controlled({"actor_id":None}, request, self.data)["response"]["status"], 401)

    def test_no_payload_on_any_denial(self):
        lesson = run_lesson()
        for row in lesson["matrix_runs"] + lesson["boundary_runs"]:
            result = row["controlled"]["response"]
            if result["status"] != 200:
                self.assertEqual(set(result["body"]), {"error"})

    def test_trace_shows_enforcement_and_disabled_bug_control(self):
        c, q = {"actor_id":"actor-a"}, {"object_id":"red-report","operation":"read"}
        good = controlled(c, q, self.data)["decision"]["trace"]
        self.assertEqual([s["control"] for s in good], ["request-schema","authenticated-context","supported-operation","object-lookup","tenant-boundary","operation-resource-grant"])
        self.assertTrue(all(s["passed"] for s in good))
        self.assertFalse(lookup_only(c, q, self.data)["decision"]["trace"][-1]["enabled"])

    def test_pure_handler_and_no_response_alias(self):
        before = deepcopy(self.data)
        context, request = {"actor_id":"actor-a"}, {"object_id":"red-report","operation":"read"}
        original_request = deepcopy(request)
        result = controlled(context, request, self.data)
        result["response"]["body"]["payload"] = "modified output only"
        self.assertEqual(self.data, before)
        self.assertEqual(request, original_request)

    def test_deterministic_no_external_security_credit(self):
        self.assertEqual(run_lesson(), run_lesson())
        self.assertFalse(run_lesson()["external_attack_performed"])
        self.assertEqual(run_lesson()["subject_completion"], "not-claimed")


if __name__ == "__main__":
    unittest.main()
