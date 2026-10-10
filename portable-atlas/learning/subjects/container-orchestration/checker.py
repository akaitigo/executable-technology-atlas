"""Independent enumeration/invariant oracle; saved-file reads only, no model import."""
import copy
import hashlib
import itertools
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NODES = ("node-a", "node-b")


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def input_reason(req, state):
    if not isinstance(req, dict) or set(req) != {"desired_replicas", "health", "expected_revision"}:
        return "invalid-request-schema"
    count = req["desired_replicas"]
    if isinstance(count, bool) or not isinstance(count, int) or count < 0 or count > 6:
        return "invalid-replicas"
    if not isinstance(req["health"], dict) or set(req["health"]) != set(NODES) or any(not isinstance(v, bool) for v in req["health"].values()):
        return "invalid-node-health"
    if not isinstance(state, dict) or set(state) != {"revision", "pods"} or type(state["revision"]) is not int or state["revision"] < 0 or not isinstance(state["pods"], list):
        return "invalid-state-schema"
    if type(req["expected_revision"]) is not int or req["expected_revision"] != state["revision"]:
        return "stale-revision"
    seen = set()
    occupancy = dict.fromkeys(NODES, 0)
    for pod in state["pods"]:
        if not isinstance(pod, dict) or set(pod) != {"id", "node"} or not re.fullmatch(r"pod-[1-6]", str(pod["id"])) or pod["node"] not in (None, *NODES):
            return "invalid-pod"
        if pod["id"] in seen:
            return "duplicate-pod"
        seen.add(pod["id"])
        if pod["node"]:
            occupancy[pod["node"]] += 1
    if max(occupancy.values()) > 2:
        return "invalid-input-overcommit"
    return None


def enumerate_optimum(req, before):
    """Enumerate every assignment; independent of producer greedy filter/score loop."""
    count = req["desired_replicas"]
    ids = ["pod-" + str(i) for i in range(1, count + 1)]
    fixed = {p["id"]: p["node"] for p in before["pods"] if p["id"] in ids and p["node"] and req["health"][p["node"]]}
    choices = (None,) + tuple(n for n in NODES if req["health"][n])
    feasible, best = 0, -1
    for assignment in itertools.product(choices, repeat=count):
        if any(assignment[ids.index(i)] != n for i, n in fixed.items()):
            continue
        if any(assignment.count(n) > 2 for n in NODES):
            continue
        feasible += 1
        best = max(best, sum(n is not None for n in assignment))
    if best < 0:
        raise ValueError("no valid assignment")
    return {"enumerated_candidates": len(choices) ** count, "feasible_assignments": feasible, "maximum_bound": best,
            "minimum_pending": count - best, "preserved_healthy": fixed}


def violations(req, before, after):
    issues = []
    ids = [p["id"] for p in after["pods"]]
    expected = ["pod-" + str(i) for i in range(1, req["desired_replicas"] + 1)]
    if sorted(ids) != expected or len(set(ids)) != len(ids):
        issues.append("pod-identity-set")
    for n in NODES:
        if sum(p["node"] == n for p in after["pods"]) > 2:
            issues.append("capacity:" + n)
    if any(p["node"] is not None and (p["node"] not in NODES or not req["health"][p["node"]]) for p in after["pods"]):
        issues.append("unhealthy-or-unknown-node")
    opt = enumerate_optimum(req, before)
    bound = sum(p["node"] is not None for p in after["pods"])
    if bound != opt["maximum_bound"]:
        issues.append("not-feasible-optimum")
    mapping = {p["id"]: p["node"] for p in after["pods"]}
    if any(mapping.get(i) != n for i, n in opt["preserved_healthy"].items()):
        issues.append("healthy-placement-moved")
    return issues


def replay_events(before, events):
    pods = {p["id"]: p["node"] for p in before["pods"]}
    for e in events:
        if e["event"] == "delete-model-pod":
            if pods[e["id"]] != e["previous_node"]:
                raise ValueError("delete binding mismatch")
            del pods[e["id"]]
        elif e["event"] == "create-model-pod":
            if e["id"] in pods:
                raise ValueError("duplicate create")
            pods[e["id"]] = None
        elif e["event"] == "unbind-failed-node":
            if pods[e["id"]] != e["previous_node"]:
                raise ValueError("unbind mismatch")
            pods[e["id"]] = None
        elif e["event"] == "bind-model-pod":
            if pods[e["id"]] is not None:
                raise ValueError("bind occupied pod")
            pods[e["id"]] = e["node"]
        elif e["event"] not in ("filter", "pending"):
            raise ValueError("unknown event")
    return [{"id": i, "node": pods[i]} for i in sorted(pods)]


def load():
    text = (ROOT / "observation-data.js").read_text()
    data = json.loads(text.removeprefix("window.SCHEDULER_OBSERVATION = ").strip().removesuffix(";"))
    if not re.fullmatch(r"observations/[0-9TZ]+-scheduler", data["directory"]):
        raise ValueError("unsafe observation path")
    return data, ROOT / data["directory"]


def oracle_report(folder):
    observation = json.loads((folder / "observation.json").read_bytes())
    rows = []
    for row in observation["scenarios"]:
        req, before, result = row["input"]["request"], row["input"]["state"], row["result"]
        reason = input_reason(req, before)
        if reason:
            problems = [] if result["reason"] == reason and result["outcome"] == "blocked" and result["state"] == before else ["invalid-input-mutated-or-not-blocked"]
            optimum = None
        else:
            problems = violations(req, before, result["state"])
            optimum = enumerate_optimum(req, before)
            if replay_events(before, result["events"]) != result["state"]["pods"]:
                problems.append("event-state-mismatch")
        rows.append({"id": row["id"], "verdict": "rejected" if problems else "blocked-unchanged" if reason else "valid",
                     "violations": problems, "enumeration": optimum, "input_digest": sha(encoded(row["input"])), "result_digest": sha(encoded(result))})
    return {"execution_id": observation["execution_id"], "oracle": "independent-enumeration-and-invariants",
            "checker_source_digest": sha((ROOT / "checker.py").read_bytes()), "rows": rows}


class SchedulerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload, cls.folder = load()
        cls.obs = cls.payload["observation"]
        cls.rows = {r["id"]: r for r in cls.obs["scenarios"]}

    def test_actual_outcomes_and_independent_enumeration(self):
        expected = {"create": "bound", "scale-up": "bound", "scale-down": "bound", "node-failure-fit": "bound",
                    "node-failure-pending": "pending", "node-recovery": "bound", "over-capacity": "pending", "both-down": "pending", "zero": "bound",
                    "stale-revision": "blocked", "invalid-negative": "blocked", "invalid-bool": "blocked", "unknown-node": "blocked", "duplicate-pod": "blocked",
                    "bad-over-capacity": "bound", "bad-failure": "bound"}
        self.assertEqual(set(expected), set(self.rows))
        for ident, row in self.rows.items():
            with self.subTest(case=ident):
                inp, result = row["input"], row["result"]
                req, before = inp["request"], inp["state"]
                self.assertEqual(inp["capacity"], {"node-a": 2, "node-b": 2})
                self.assertEqual(result["outcome"], expected[ident])
                reason = input_reason(req, before)
                self.assertEqual(result["reason"], reason)
                if reason:
                    self.assertEqual(result["state"], before)
                    self.assertFalse(result["changed"])
                    continue
                found = violations(req, before, result["state"])
                if ident.startswith("bad-"):
                    self.assertIn("not-feasible-optimum", found)
                    self.assertTrue(any(x.startswith("capacity:") for x in found))
                else:
                    self.assertEqual(found, [])
                    pending = sum(p["node"] is None for p in result["state"]["pods"])
                    self.assertEqual(result["outcome"], "pending" if pending else "bound")

    def test_events_revision_and_hash_bindings(self):
        for row in self.rows.values():
            before, result = row["input"]["state"], row["result"]
            self.assertEqual(result["pre_digest"], sha(encoded(before)))
            self.assertEqual(result["post_digest"], sha(encoded(result["state"])))
            if result["outcome"] != "blocked":
                self.assertEqual(replay_events(before, result["events"]), result["state"]["pods"])
                changed = before["pods"] != result["state"]["pods"]
                self.assertEqual(result["changed"], changed)
                self.assertEqual(result["state"]["revision"], before["revision"] + int(changed))

    def test_idempotent_bound_and_pending_reconcile(self):
        for row in self.rows.values():
            if row["second"]:
                self.assertEqual(row["second"]["state"], row["result"]["state"])
                self.assertFalse(row["second"]["changed"])
                self.assertEqual(row["second"]["pre_digest"], row["second"]["post_digest"])
                self.assertFalse(any(e["event"] in ("create-model-pod", "delete-model-pod", "bind-model-pod", "unbind-failed-node") for e in row["second"]["events"]))
        self.assertIsNotNone(self.rows["node-failure-pending"]["second"])

    def test_failure_recovery_and_healthy_survivor_binding(self):
        fit = self.rows["node-failure-fit"]["result"]
        self.assertEqual([p["node"] for p in fit["state"]["pods"]], ["node-b", "node-b"])
        failed = self.rows["node-failure-pending"]["result"]["state"]
        recovery = self.rows["node-recovery"]
        self.assertEqual(failed, recovery["input"]["state"])
        self.assertEqual([p["node"] for p in recovery["result"]["state"]["pods"]], ["node-a", "node-b", "node-a", "node-b"])
        self.assertEqual(self.rows["over-capacity"]["result"]["state"]["pods"][-1]["node"], None)

    def test_fresh_negative_oracle_mutations(self):
        r = self.rows["scale-up"]
        before, req = r["input"]["state"], r["input"]["request"]
        bad = copy.deepcopy(r["result"]["state"])
        bad["pods"][1]["node"] = "node-a"
        self.assertIn("capacity:node-a", violations(req, before, bad))
        bad = copy.deepcopy(r["result"]["state"])
        bad["pods"].pop()
        self.assertIn("pod-identity-set", violations(req, before, bad))
        bad = copy.deepcopy(r["result"]["state"])
        bad["pods"][0]["node"] = "node-x"
        self.assertIn("unhealthy-or-unknown-node", violations(req, before, bad))
        events = [e for e in r["result"]["events"] if e["event"] != "bind-model-pod"]
        self.assertNotEqual(replay_events(before, events), r["result"]["state"]["pods"])

    def test_full_finite_capacity_denominator_and_invalid_boundaries(self):
        for count in range(7):
            for flags in itertools.product((False, True), repeat=2):
                req = {"desired_replicas": count, "health": dict(zip(NODES, flags)), "expected_revision": 0}
                opt = enumerate_optimum(req, {"revision": 0, "pods": []})
                self.assertEqual(opt["maximum_bound"], min(count, 2 * sum(flags)))
                self.assertEqual(opt["minimum_pending"], max(0, count - 2 * sum(flags)))
        inp = self.rows["create"]["input"]
        for value in (-1, 7, True, 1.5, None, "2"):
            req = {**inp["request"], "desired_replicas": value}
            self.assertEqual(input_reason(req, inp["state"]), "invalid-replicas")
        self.assertEqual(input_reason({**inp["request"], "extra": 0}, inp["state"]), "invalid-request-schema")

    def test_raw_index_input_source_command_and_runtime(self):
        index = json.loads((self.folder / "artifact-index.json").read_bytes())
        self.assertEqual(set(index) | {"artifact-index.json"}, {p.relative_to(self.folder).as_posix() for p in self.folder.rglob("*") if p.is_file()})
        for name, meta in index.items():
            raw = (self.folder / name).read_bytes()
            self.assertEqual(meta, {"digest": sha(raw), "size": len(raw)})
        for name, d in self.obs["source_bindings"].items():
            self.assertEqual(sha((ROOT / name).read_bytes()), d)
        command = json.loads((self.folder / "command.json").read_bytes())
        self.assertEqual(command["exit_code"], 0)
        self.assertEqual(json.loads(command["stdout"]), self.obs)
        self.assertEqual(command["stdout_digest"], sha(command["stdout"].encode()))
        self.assertEqual(command["stderr_digest"], sha(command["stderr"].encode()))
        self.assertEqual((self.obs["attempts"], self.obs["retries"], self.obs["containers_started"], self.obs["external_mutations"]), (1, 0, 0, 0))
        self.assertFalse(self.obs["real_kubernetes_executed"])
        oracle = json.loads((self.folder / "oracle-report.json").read_bytes())
        self.assertEqual(oracle, oracle_report(self.folder))
        self.assertEqual([r["id"] for r in oracle["rows"] if r["verdict"] == "rejected"], ["bad-over-capacity", "bad-failure"])
        oracle_command = json.loads((self.folder / "oracle-command.json").read_bytes())
        self.assertEqual(oracle_command["exit_code"], 0)
        self.assertEqual(json.loads(oracle_command["stdout"]), oracle)
        self.assertEqual(oracle_command["stdout_digest"], sha(oracle_command["stdout"].encode()))
        self.assertEqual(oracle_command["stderr_digest"], sha(oracle_command["stderr"].encode()))
        for row in self.rows.values():
            folder = self.folder / row["id"]
            self.assertEqual(json.loads((folder / "input.json").read_bytes()), row["input"])
            self.assertEqual(json.loads((folder / "result.json").read_bytes()), row["result"])
            self.assertEqual((folder / "after-state.json").read_bytes(), encoded(row["result"]["state"]))
            self.assertEqual(json.loads((folder / "events.json").read_bytes()), row["result"]["events"])
            if row["second"]:
                self.assertEqual(json.loads((folder / "second-result.json").read_bytes()), row["second"])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--oracle-json":
        if not re.fullmatch(r"observations/[0-9TZ]+-scheduler", sys.argv[2]):
            raise SystemExit("invalid observation path")
        print(json.dumps(oracle_report(ROOT / sys.argv[2]), ensure_ascii=False, separators=(",", ":")))
    else:
        unittest.main(verbosity=2)
