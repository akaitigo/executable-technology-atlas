"""Independent hand oracle + direct read-only SQLite checks. No producer import."""
import copy
import hashlib
import json
import re
import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# effect rows, balance, inbox keys, model acks, model DLQ, deliveries, model retries, outcome
EXPECTED = {
    "normal": (1, 7, 1, 1, 0, 1, 0, "acknowledged"),
    "naive-crash": (2, 14, 0, 1, 0, 2, 1, "acknowledged"),
    "inbox-crash": (1, 7, 1, 1, 0, 2, 1, "acknowledged"),
    "same-id-replay": (1, 7, 1, 2, 0, 2, 0, "acknowledged"),
    "same-id-conflict": (1, 7, 1, 1, 1, 2, 0, "dlq"),
    "distinct-id": (2, 14, 2, 2, 0, 2, 0, "acknowledged"),
    "poison-3": (0, 0, 0, 0, 1, 3, 2, "dlq"),
    "poison-1": (0, 0, 0, 0, 1, 1, 0, "dlq"),
    "transient-success": (1, 7, 1, 1, 0, 3, 2, "acknowledged"),
    "transient-exhausted": (0, 0, 0, 0, 1, 2, 1, "dlq"),
    "invalid-limit-zero": (0, 0, 0, 0, 0, 0, 0, "blocked"),
    "invalid-limit-bool": (0, 0, 0, 0, 0, 0, 0, "blocked"),
    "invalid-id": (0, 0, 0, 0, 0, 0, 0, "blocked"),
    "zero-delta": (1, 0, 1, 1, 0, 1, 0, "acknowledged"),
}


def raw_sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def sql_state(path):
    # Final task-owned DB is closed and journal-free. These flags prohibit writes/creation.
    with sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
        balance = db.execute("SELECT balance FROM account WHERE id='demo'").fetchone()[0]
        effects = [{"sequence": s, "event_id": i, "delta": d} for s, i, d in db.execute("SELECT sequence,event_id,delta FROM effects ORDER BY sequence")]
        inbox = [{"event_id": i, "fingerprint": f, "payload": json.loads(p)} for i, f, p in db.execute("SELECT event_id,fingerprint,payload FROM inbox ORDER BY event_id")]
    return {"balance": balance, "effects": effects, "inbox": inbox}, integrity


def summarize(state, result):
    return (len(state["effects"]), state["balance"], len(state["inbox"]), len(result["acknowledgements"]), len(result["dlq"]),
            result["deliveries"], result["model_retries"], result["outcome"])


def effect_invariants(state, policy):
    issues = []
    if sum(row["delta"] for row in state["effects"]) != state["balance"]:
        issues.append("balance-effect-sum")
    ids = [e["event_id"] for e in state["effects"]]
    if len(ids) != len(set(ids)):
        issues.append("duplicate-effect")
    if policy == "inbox":
        keys = [e["event_id"] for e in state["inbox"]]
        if sorted(ids) != sorted(keys):
            issues.append("inbox-effect-atomicity")
        by_id = {e["event_id"]: e for e in state["effects"]}
        for row in state["inbox"]:
            if row["fingerprint"] != raw_sha(encoded(row["payload"])) or by_id.get(row["event_id"], {}).get("delta") != row["payload"]["delta"]:
                issues.append("payload-fingerprint-effect-binding")
    return issues


def report(folder):
    observation = json.loads((folder / "observation.json").read_bytes())
    if {r["id"] for r in observation["scenarios"]} != set(EXPECTED):
        raise ValueError("scenario denominator mismatch")
    rows = []
    for row in observation["scenarios"]:
        state, integrity = sql_state(folder / row["id"] / "consumer.sqlite")
        result = row["result"]
        actual = summarize(state, result)
        issues = effect_invariants(state, row["input"]["policy"])
        rows.append({"id": row["id"], "expected": list(EXPECTED[row["id"]]), "actual": list(actual),
                     "matches_expected": actual == EXPECTED[row["id"]] and state == result["state"] and integrity == "ok",
                     "effect_invariant_violations": issues, "verdict": "duplicate-effect" if issues else "blocked-unchanged" if result["outcome"] == "blocked" else "conflict-held" if row["id"] == "same-id-conflict" else "single-effect" if state["effects"] else "no-effect",
                     "sqlite_integrity": integrity, "database_digest": raw_sha((folder / row["id"] / "consumer.sqlite").read_bytes()),
                     "input_digest": raw_sha(encoded(row["input"])), "result_digest": raw_sha(encoded(result))})
    return {"execution_id": observation["execution_id"], "oracle": "independent-hand-expectations-and-read-only-sqlite",
            "checker_source_digest": raw_sha((ROOT / "checker.py").read_bytes()), "rows": rows}


def load():
    text = (ROOT / "observation-data.js").read_text()
    data = json.loads(text.removeprefix("window.EVENT_OBSERVATION = ").strip().removesuffix(";"))
    if not re.fullmatch(r"observations/[0-9TZ]+-events", data["directory"]):
        raise ValueError("unsafe observation path")
    return data, ROOT / data["directory"]


class EventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload, cls.folder = load()
        cls.obs = cls.payload["observation"]
        cls.rows = {r["id"]: r for r in cls.obs["scenarios"]}

    def test_all_actual_sqlite_effects_against_hand_oracle(self):
        self.assertEqual(set(self.rows), set(EXPECTED))
        actual_report = report(self.folder)
        for row in actual_report["rows"]:
            self.assertTrue(row["matches_expected"], row["id"])
            self.assertEqual(row["effect_invariant_violations"], ["duplicate-effect"] if row["id"] == "naive-crash" else [])
        self.assertEqual(actual_report, self.payload["oracle"])
        self.assertEqual(actual_report, json.loads((self.folder / "oracle-report.json").read_bytes()))

    def test_real_process_crash_commit_then_replay(self):
        for ident, effects in (("naive-crash", 2), ("inbox-crash", 1)):
            records = json.loads((self.folder / ident / "delivery-records.json").read_bytes())
            first, replay = records
            self.assertEqual((first["exit_code"], replay["exit_code"]), (70, 0))
            self.assertEqual(first["db_after"]["balance"], 7)
            self.assertEqual(len(first["db_after"]["effects"]), 1)
            self.assertEqual(replay["db_before"], first["db_after"])
            self.assertEqual(len(replay["db_after"]["effects"]), effects)
            kinds = [e["event"] for e in first["trace"]]
            self.assertLess(kinds.index("transaction-committed"), kinds.index("injected-process-crash-before-ack"))
            self.assertNotIn("ack-eligible", kinds)
            self.assertTrue(any(e["event"] == "sqlite-sql" and e["sql"] == "COMMIT" for e in first["trace"]))
            self.assertNotEqual(first["trace"][0]["pid"], replay["trace"][0]["pid"])
        safe = json.loads((self.folder / "inbox-crash" / "delivery-records.json").read_bytes())[1]
        self.assertEqual(safe["db_pre_digest"], safe["db_post_digest"])
        self.assertIn("duplicate-no-effect", [e["event"] for e in safe["trace"]])

    def test_identity_payload_conflict_and_zero_boundary(self):
        row = self.rows["same-id-conflict"]
        records = json.loads((self.folder / row["id"] / "delivery-records.json").read_bytes())
        self.assertEqual(records[1]["exit_code"], 66)
        self.assertEqual(records[1]["db_before"], records[1]["db_after"])
        self.assertEqual(row["result"]["dlq"][0]["message"]["payload"]["delta"], 9)
        self.assertEqual(row["result"]["state"]["inbox"][0]["payload"]["delta"], 7)
        self.assertEqual(row["result"]["model_retries"], 0)
        self.assertEqual(len(self.rows["distinct-id"]["result"]["state"]["effects"]), 2)
        self.assertEqual(len(self.rows["zero-delta"]["result"]["state"]["effects"]), 1)
        self.assertEqual(self.rows["zero-delta"]["result"]["state"]["balance"], 0)

    def test_poison_and_transient_bounded_retry_dlq(self):
        for ident in ("poison-3", "poison-1", "transient-success", "transient-exhausted"):
            row = self.rows[ident]
            records = json.loads((self.folder / ident / "delivery-records.json").read_bytes())
            self.assertLessEqual(len(records), row["input"]["max_deliveries"])
            self.assertEqual([r["attempt"] for r in records], list(range(1, len(records) + 1)))
            for r in records:
                if r["exit_code"] in (65, 75):
                    self.assertEqual(r["db_before"], r["db_after"])
                    self.assertNotIn("ack-eligible", [e["event"] for e in r["trace"]])
                if r["exit_code"] == 75:
                    self.assertTrue(any(e["event"] == "sqlite-sql" and e["sql"].startswith("INSERT INTO inbox") for e in r["trace"]))
                    self.assertTrue(any(e["event"] == "sqlite-sql" and e["sql"] == "ROLLBACK" for e in r["trace"]))
            if row["result"]["dlq"]:
                self.assertEqual(row["result"]["dlq"][0]["attempts"], row["input"]["max_deliveries"])

    def test_delivery_trace_ack_binding_and_attempt_snapshot_chain(self):
        for row in self.rows.values():
            records = json.loads((self.folder / row["id"] / "delivery-records.json").read_bytes())
            self.assertEqual(len(records), row["result"]["deliveries"])
            before = {"balance": 0, "effects": [], "inbox": []}
            for r in records:
                self.assertEqual(r["db_before"], before)
                before = r["db_after"]
                self.assertEqual(r["trace"], [json.loads(s) for s in r["stdout"].splitlines()])
                self.assertEqual(r["stdout_digest"], raw_sha(r["stdout"].encode()))
                self.assertEqual(r["stderr_digest"], raw_sha(r["stderr"].encode()))
                self.assertEqual(r["stdin_digest"], raw_sha(json.dumps(r["request"]).encode()))
                self.assertLessEqual(datetime.fromisoformat(r["started_at"].replace("Z", "+00:00")), datetime.fromisoformat(r["completed_at"].replace("Z", "+00:00")))
            self.assertEqual(before, row["result"]["state"])
            self.assertEqual([a["delivery"] for a in row["result"]["acknowledgements"]], [r["delivery"] for r in records if r["exit_code"] == 0])
            if row["result"]["outcome"] == "blocked":
                self.assertEqual(records, [])

    def test_fresh_duplicate_missing_marker_payload_mutations(self):
        state = copy.deepcopy(self.rows["normal"]["result"]["state"])
        state["effects"].append({"sequence": 2, "event_id": "event-a", "delta": 7})
        state["balance"] = 14
        self.assertIn("duplicate-effect", effect_invariants(state, "inbox"))
        state = copy.deepcopy(self.rows["normal"]["result"]["state"])
        state["inbox"].clear()
        self.assertIn("inbox-effect-atomicity", effect_invariants(state, "inbox"))
        state = copy.deepcopy(self.rows["normal"]["result"]["state"])
        state["inbox"][0]["payload"]["delta"] = 9
        self.assertIn("payload-fingerprint-effect-binding", effect_invariants(state, "inbox"))
        state = copy.deepcopy(self.rows["normal"]["result"]["state"])
        state["balance"] = 0
        self.assertIn("balance-effect-sum", effect_invariants(state, "inbox"))

    def test_raw_artifact_input_source_runtime_binding(self):
        index = json.loads((self.folder / "artifact-index.json").read_bytes())
        files = {p.relative_to(self.folder).as_posix() for p in self.folder.rglob("*") if p.is_file()}
        self.assertEqual(set(index) | {"artifact-index.json"}, files)
        self.assertFalse(any(n.endswith(("-journal", "-wal", "-shm")) for n in files))
        for name, metadata in index.items():
            raw = (self.folder / name).read_bytes()
            self.assertEqual(metadata, {"digest": raw_sha(raw), "size": len(raw)})
        for name, digest in self.obs["source_bindings"].items():
            self.assertEqual(raw_sha((ROOT / name).read_bytes()), digest)
        for name, expected in (("command.json", self.obs), ("oracle-command.json", self.payload["oracle"])):
            command = json.loads((self.folder / name).read_bytes())
            self.assertEqual(command["exit_code"], 0)
            self.assertEqual(json.loads(command["stdout"]), expected)
            self.assertEqual(command["stdout_digest"], raw_sha(command["stdout"].encode()))
            self.assertEqual(command["stderr_digest"], raw_sha(command["stderr"].encode()))
        self.assertEqual((self.obs["attempts"], self.obs["outer_retries"], self.obs["external_effects"]), (1, 0, 0))
        self.assertFalse(self.obs["real_broker_executed"])
        for row in self.rows.values():
            folder = self.folder / row["id"]
            self.assertEqual(json.loads((folder / "input.json").read_bytes()), row["input"])
            self.assertEqual(json.loads((folder / "result.json").read_bytes()), row["result"])
            self.assertEqual(json.loads((folder / "after-state.json").read_bytes()), row["result"]["state"])
            self.assertEqual(json.loads((folder / "events.json").read_bytes()), row["result"]["events"])


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--oracle-json":
        if not re.fullmatch(r"observations/[0-9TZ]+-events", sys.argv[2]):
            raise SystemExit("invalid observation path")
        print(json.dumps(report(ROOT / sys.argv[2]), ensure_ascii=False, separators=(",", ":")))
    else:
        unittest.main(verbosity=2)
