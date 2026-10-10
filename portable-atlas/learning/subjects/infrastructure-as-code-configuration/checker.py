"""Independent saved-file oracle. No import of simulator or experiment; no writes."""
import copy
import hashlib
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha_bytes(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def value_sha(value):
    return sha_bytes((json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode())


def schema_reason(doc, state=False):
    keys = {"scope", "resources", "revision"} if state else {"scope", "resources"}
    if type(doc) is not dict or set(doc) != keys or doc["scope"] != "synthetic-iac-v1":
        return "unsupported-root-schema"
    if state and (type(doc["revision"]) is not int or doc["revision"] < 0):
        return "invalid-revision"
    if type(doc["resources"]) is not dict or len(doc["resources"]) > 6:
        return "resource-limit-or-type"
    for ident, attrs in doc["resources"].items():
        if not re.fullmatch(r"(service|config)\.[a-z][a-z0-9-]{0,20}", ident):
            return "unsupported-resource-id"
        if type(attrs) is not dict:
            return "unsupported-resource-attributes"
        is_service = ident.startswith("service.")
        if set(attrs) != ({"replicas", "port", "enabled"} if is_service else {"text"}):
            return "unsupported-attribute"
        if None in attrs.values():
            return "unknown-value"
        if is_service:
            if type(attrs["replicas"]) is not int or attrs["replicas"] not in range(6):
                return "invalid-replicas"
            if type(attrs["port"]) is not int or not 1 <= attrs["port"] <= 65535 or type(attrs["enabled"]) is not bool:
                return "invalid-service-value"
        elif type(attrs["text"]) is not str or len(attrs["text"]) > 80:
            return "invalid-config-text"
    return None


def independent_diff(want, have):
    old, new = have["resources"], want["resources"]
    removed = set(old) - set(new)
    created = set(new) - set(old)
    changed = {k for k in set(old) & set(new) if old[k] != new[k]}
    return [{"id": k, "op": "delete" if k in removed else "create" if k in created else "update",
             "before": old.get(k), "after": new.get(k)} for k in sorted(removed | created | changed)]


def expected_plan(want, have):
    reason = schema_reason(want) or schema_reason(have, True)
    return {"schema_version": 1, "status": "blocked" if reason else "planned", "scope": "synthetic-iac-v1",
            "desired_digest": value_sha(want), "observed_digest": value_sha(have), "observed_revision": have.get("revision"),
            "actions": [] if reason else independent_diff(want, have), "blocked_reasons": [reason] if reason else []}


def independent_apply(plan, want, have, pin, approval):
    reason = None
    if value_sha(plan) != pin:
        reason = "plan-digest-mismatch"
    elif plan["status"] == "blocked":
        reason = plan["blocked_reasons"][0]
    elif have["revision"] != plan["observed_revision"]:
        reason = "stale-revision"
    elif value_sha(have) != plan["observed_digest"]:
        reason = "stale-observed-hash"
    elif value_sha(want) != plan["desired_digest"]:
        reason = "desired-changed"
    elif expected_plan(want, have) != plan:
        reason = "plan-actions-mismatch"
    else:
        ids = sorted(a["id"] for a in plan["actions"] if a["op"] == "delete")
        if ids and approval != {"plan_digest": pin, "delete_ids": ids}:
            reason = "delete-approval-required"
    if reason:
        return "blocked", reason, copy.deepcopy(have)
    # Alternative oracle: after validating exact actions, derive the desired final state
    # directly, rather than replaying producer's update/delete instruction loop.
    state = {"scope": have["scope"], "revision": have["revision"] + bool(plan["actions"]),
             "resources": copy.deepcopy(want["resources"])}
    return ("applied" if plan["actions"] else "noop"), None, state


def load_current():
    text = (ROOT / "observation-data.js").read_text()
    payload = json.loads(text.removeprefix("window.IAC_OBSERVATION = ").strip().removesuffix(";"))
    if not re.fullmatch(r"observations/[0-9TZ]+-iac", payload["directory"]):
        raise ValueError("unsafe observation path")
    return payload, ROOT / payload["directory"]


class IaCTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload, cls.folder = load_current()
        cls.obs = cls.payload["observation"]
        cls.rows = {r["id"]: r for r in cls.obs["scenarios"]}

    def test_all_twelve_actual_results(self):
        expected = {"noop": ("noop", None), "reconcile": ("applied", None), "drift": ("applied", None),
                    "delete-approved": ("applied", None), "stale-revision": ("blocked", "stale-revision"),
                    "silent-drift": ("blocked", "stale-observed-hash"), "delete-blocked": ("blocked", "delete-approval-required"),
                    "wrong-approval": ("blocked", "delete-approval-required"), "unknown-value": ("blocked", "unknown-value"),
                    "unsupported-attribute": ("blocked", "unsupported-attribute"), "tampered-plan": ("blocked", "plan-digest-mismatch"),
                    "desired-changed": ("blocked", "desired-changed")}
        self.assertEqual(set(expected), set(self.rows))
        for ident, row in self.rows.items():
            with self.subTest(case=ident):
                self.assertEqual(expected_plan(row["desired_planning"], row["observed_planning"]), row["plan_created"])
                result = independent_apply(row["plan_supplied"], row["desired_applying"], row["observed_current"], row["trusted_plan_digest"], row["approval"])
                self.assertEqual(result[:2], expected[ident])
                self.assertEqual(result, (row["result"]["status"], row["result"]["reason"], row["result"]["state"]))
                self.assertEqual(row["result"]["pre_digest"], value_sha(row["observed_current"]))
                self.assertEqual(row["result"]["post_digest"], value_sha(result[2]))
                if result[0] == "blocked":
                    self.assertEqual(result[2], row["observed_current"])
                    self.assertEqual(row["result"]["events"][-1]["mutation_count"], 0)

    def test_create_update_delete_diff_and_revision(self):
        r = self.rows["reconcile"]
        self.assertEqual([a["op"] for a in r["plan_created"]["actions"]], ["create", "update"])
        self.assertEqual(r["result"]["state"]["revision"], 8)
        self.assertEqual(r["result"]["state"]["resources"]["service.web"]["replicas"], 3)
        d = self.rows["delete-approved"]
        self.assertEqual(d["plan_created"]["actions"][0]["op"], "delete")
        self.assertNotIn("service.web", d["result"]["state"]["resources"])

    def test_drift_and_stale_snapshot_are_distinct(self):
        r = self.rows["drift"]
        self.assertEqual(r["baseline"]["resources"]["service.web"]["replicas"], 2)
        self.assertEqual(r["observed_planning"]["resources"]["service.web"]["replicas"], 1)
        self.assertEqual(r["plan_created"]["actions"][0]["after"]["replicas"], 2)
        self.assertEqual(r["result"]["state"]["revision"], 9)
        for case in ("stale-revision", "silent-drift"):
            r = self.rows[case]
            self.assertEqual(r["result"]["state"], r["observed_current"])
            self.assertNotEqual(r["observed_planning"], r["observed_current"])

    def test_second_reconcile_is_noop_and_exact_state(self):
        for r in self.rows.values():
            if r["result"]["status"] == "blocked":
                self.assertIsNone(r["replan"])
                continue
            second = expected_plan(r["desired_applying"], r["result"]["state"])
            self.assertEqual(second, r["replan"])
            self.assertEqual(second["actions"], [])
            self.assertEqual(independent_apply(second, r["desired_applying"], r["result"]["state"], value_sha(second), None),
                             ("noop", None, r["result"]["state"]))
            self.assertEqual(r["reapply"]["state"], r["result"]["state"])

    def test_fresh_authorization_and_unknown_negatives(self):
        r = self.rows["delete-approved"]
        for a in (True, {"plan_digest": r["trusted_plan_digest"], "delete_ids": []},
                  {"plan_digest": "sha256:" + "0" * 64, "delete_ids": ["service.web"]}):
            self.assertEqual(independent_apply(r["plan_created"], r["desired_applying"], r["observed_current"], r["trusted_plan_digest"], a)[1], "delete-approval-required")
        want = copy.deepcopy(self.rows["noop"]["desired_planning"])
        for value in (None, True, 6, -1, "2"):
            want["resources"]["service.web"]["replicas"] = value
            self.assertIsNotNone(schema_reason(want))

    def test_fresh_plan_action_tamper_even_with_repin(self):
        r = self.rows["reconcile"]
        forged = copy.deepcopy(r["plan_created"])
        forged["actions"][-1]["after"]["replicas"] = 4
        before = copy.deepcopy(r["observed_current"])
        result = independent_apply(forged, r["desired_applying"], before, value_sha(forged), None)
        self.assertEqual(result, ("blocked", "plan-actions-mismatch", before))
        self.assertEqual(before, r["observed_current"])

    def test_raw_file_index_bindings_and_canonical_bytes(self):
        index = json.loads((self.folder / "artifact-index.json").read_bytes())
        actual = {p.relative_to(self.folder).as_posix() for p in self.folder.rglob("*") if p.is_file()}
        self.assertEqual(set(index) | {"artifact-index.json"}, actual)
        for name, record in index.items():
            file = self.folder / name
            self.assertTrue(file.resolve().is_relative_to(self.folder.resolve()))
            data = file.read_bytes()
            self.assertEqual(record, {"digest": sha_bytes(data), "size": len(data)})
        for source, binding in self.obs["source_bindings"].items():
            self.assertEqual(sha_bytes((ROOT / source).read_bytes()), binding)
        command = json.loads((self.folder / "command.json").read_bytes())
        self.assertEqual(command["exit_code"], 0)
        self.assertEqual(command["stderr"], "")
        self.assertEqual(json.loads(command["stdout"]), self.obs)
        self.assertEqual(sha_bytes(command["stdout"].encode()), command["stdout_digest"])
        for ident, r in self.rows.items():
            self.assertEqual(r["trusted_plan_digest"], value_sha(r["plan_created"]))
            self.assertEqual(json.loads((self.folder / ident / "trusted-plan-pin.json").read_bytes())["digest"], r["trusted_plan_digest"])
            files = {"desired-planning.json": r["desired_planning"], "desired-applying.json": r["desired_applying"],
                     "observed-planning.json": r["observed_planning"], "observed-current.json": r["observed_current"],
                     "plan-created.json": r["plan_created"], "plan-supplied.json": r["plan_supplied"],
                     "approval.json": r["approval"], "synthetic-store-after.json": r["result"]["state"], "apply-result.json": r["result"]}
            for name, value in files.items():
                raw = (self.folder / ident / name).read_bytes()
                self.assertEqual(json.loads(raw), value)
                self.assertEqual(sha_bytes(raw), value_sha(value))


if __name__ == "__main__":
    unittest.main(verbosity=2)
