#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Read-only verification with an independent state-machine oracle."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = ("kv.py", "experiment.py", "observe.py", "verify.py", "sources.json", "index.html", "app.js", "style.css")
READ = "SELECT value, version FROM kv WHERE key = ?"
STATE = "SELECT key, value, version FROM kv ORDER BY key"
CAS = "UPDATE kv SET value = ?, version = version + 1 WHERE key = ? AND version = ?"
BLIND = "UPDATE kv SET value = ?, version = version + 1 WHERE key = ?"
SEED = "INSERT INTO kv(key, value, version) VALUES (?, ?, ?)"
SCHEDULES = {
    "blind": [("A", "read"), ("B", "read"), ("A", "blind"), ("B", "blind")],
    "cas": [("A", "read"), ("B", "read"), ("A", "cas"), ("B", "cas"), ("B", "read"), ("B", "cas")],
    "invalid-types": [("A", "invalid-input")] * 6,
    "unknown-key": [("A", "read"), ("A", "cas"), ("A", "cas")],
    "aba": [("A", "read"), ("B", "cas"), ("B", "cas"), ("A", "cas")],
    "aba-reset": [("A", "read"), ("B", "delete"), ("B", "recreate"), ("A", "cas")],
}


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def validate(raw):
    assert raw["subject"] == "operational-data-stores"
    assert raw["runtime"]["engine"] == "SQLite" and raw["runtime"]["sqlite_version"] == "3.51.0"
    assert raw["runtime"]["sqlite_source_id"] and raw["runtime"]["python_version"]
    setup = raw["setup"]
    assert setup["schema_sql"] == "CREATE TABLE kv (key TEXT PRIMARY KEY NOT NULL, value INTEGER NOT NULL CHECK(typeof(value) = 'integer'), version INTEGER NOT NULL CHECK(typeof(version) = 'integer' AND version >= 0))"
    assert setup["seed_sql"] == SEED and setup["seed_parameters"] == ["counter", 0, 1]
    assert setup["session_count_per_scenario"] == 2 and setup["isolation_level"] is None
    assert setup["schedule"] == "fixed sequential autocommit statements; no parallel threads"
    assert [case["id"] for case in raw["scenarios"]] == list(SCHEDULES)
    cases = {}
    for case in raw["scenarios"]:
        cases[case["id"]] = case
        assert case["connection_count"] == 2 and case["distinct_connection_objects"] is True
        assert case["database_uri"] == "file:atlas_kv_" + case["id"] + "?mode=memory&cache=shared"
        assert case["initial"] == [["counter", 0, 1]] and case["final_sql"] == STATE
        assert [(step["session"], step["operation"]) for step in case["trace"]] == SCHEDULES[case["id"]]
        state = {"counter": [0, 1]}
        for number, step in enumerate(case["trace"], 1):
            assert step["step"] == number and step["autocommit_transaction_open_after"] is False
            assert step["state_sql"] == STATE
            operation, params = step["operation"], step["parameters"]
            sql = {"read": READ, "cas": CAS, "blind": BLIND, "delete": "DELETE FROM kv WHERE key = ?", "recreate": SEED, "invalid-input": None}[operation]
            assert step["sql"] == sql
            rows, count = [], 0
            if operation == "read":
                count = -1
                rows = [state[params[0]].copy()] if params[0] in state else []
            elif operation in ("blind", "cas"):
                value, key = params[:2]
                if key in state and (operation == "blind" or state[key][1] == params[2]):
                    state[key] = [value, state[key][1] + 1]
                    count = 1
            elif operation == "delete":
                if params[0] in state:
                    del state[params[0]]
                    count = 1
            elif operation == "recreate":
                key, value, version = params
                assert key not in state
                state[key] = [value, version]
                count = 1
            else:
                value, key, version = params
                valid = (type(key) is str and bool(key) and type(value) is int and
                         -(2**63) <= value < 2**63 and type(version) is int and 0 <= version < 2**63-1)
                assert not valid and step["reason"]
                count = None
            assert step["rows"] == rows and step["rowcount"] == count
            snapshot = [[key] + state[key] for key in sorted(state)]
            assert step["state_after"] == snapshot, "recorded DB state differs from independent transition"
        assert case["final"] == [[key] + state[key] for key in sorted(state)]
    assert cases["blind"]["final"] == [["counter", 1, 3]]
    assert [step["parameters"] for step in cases["blind"]["trace"][2:]] == [[1, "counter"], [1, "counter"]]
    assert cases["cas"]["trace"][3]["parameters"] == [1, "counter", 1]
    assert cases["cas"]["trace"][3]["rowcount"] == 0
    assert cases["cas"]["final"] == [["counter", 2, 3]]
    assert cases["unknown-key"]["trace"][0]["rows"] == []
    assert [step["rowcount"] for step in cases["unknown-key"]["trace"]] == [-1, 0, 0]
    assert cases["unknown-key"]["final"] == [["counter", 0, 1]]
    assert cases["invalid-types"]["final"] == [["counter", 0, 1]]
    assert [step["parameters"] for step in cases["invalid-types"]["trace"]] == [
        [1, "counter", "1"], [1, "counter", True], [1, "counter", -1],
        [1.5, "counter", 1], ["1", "counter", 1], [True, "counter", 1]]
    assert cases["aba"]["final"] == [["counter", 0, 3]] and cases["aba"]["trace"][-1]["rowcount"] == 0
    assert cases["aba-reset"]["final"] == [["counter", 1, 2]] and cases["aba-reset"]["trace"][-1]["rowcount"] == 1
    assert raw["scope"] == {"actual": "two SQLite connections to named shared in-memory databases",
        "locking_tested": False, "parallel_performance_measured": False, "redis_executed": False,
        "cache_document_graph_implemented": False, "aba_key_recreation_protected": False}


def validate_saved(root=HERE):
    folder = root / "evidence"
    inventory = json.loads((folder / "artifacts.json").read_text())
    assert set(inventory) == {"stdout.json", "stderr.txt", "run.json", "data.js"}
    assert {path.name for path in folder.iterdir()} == set(inventory) | {"artifacts.json"}
    for name, binding in inventory.items():
        content = (folder / name).read_bytes()
        assert binding == {"digest": digest(content), "bytes": len(content)}, "artifact binding mismatch: " + name
    raw = json.loads((folder / "stdout.json").read_text())
    report = json.loads((folder / "run.json").read_text())
    validate(raw)
    assert report["runtime"] == raw["runtime"] and report["status"] == "passed"
    assert report["process"] == {"attempts": 1, "retries": 0, "exit_code": 0}
    assert report["input"] == raw["setup"]
    assert set(report["source_digests"]) == set(INPUTS)
    for name in INPUTS:
        assert digest((root / name).read_bytes()) == report["source_digests"][name], "stale source: " + name
    assert report["stdout_digest"] == digest((folder / "stdout.json").read_bytes())
    expected_js = "window.KV_LESSON = " + json.dumps({"raw": raw, "run": report}, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + ";\n"
    assert (folder / "data.js").read_text() == expected_js
    sources = json.loads((root / "sources.json").read_text())
    assert sources["third_party_body_saved"] is False
    assert len(sources["sources"]) == 4
    return raw


def negatives(raw):
    mutations = {
        "blind-success-invented": lambda x: x["scenarios"][0].__setitem__("final", [["counter", 2, 3]]),
        "stale-cas-accepted": lambda x: x["scenarios"][1]["trace"][3].__setitem__("rowcount", 1),
        "missing-trace": lambda x: x["scenarios"][1]["trace"].pop(),
        "single-session-disguised": lambda x: x["scenarios"][0].__setitem__("connection_count", 1),
        "bool-coercion": lambda x: x["scenarios"][2]["trace"][1].__setitem__("operation", "cas"),
        "unknown-key-created": lambda x: x["scenarios"][3].__setitem__("final", [["counter", 0, 1], ["missing", 1, 2]]),
        "aba-stale-accepted": lambda x: x["scenarios"][4]["trace"][-1].__setitem__("rowcount", 1),
        "aba-recreation-hidden": lambda x: x["scope"].__setitem__("aba_key_recreation_protected", True),
        "real-locking-overclaim": lambda x: x["scope"].__setitem__("locking_tested", True),
        "missing-scenario": lambda x: x["scenarios"].pop(),
    }
    for name, mutate in mutations.items():
        candidate = copy.deepcopy(raw)
        mutate(candidate)
        try:
            validate(candidate)
        except (AssertionError, KeyError, TypeError):
            continue
        raise AssertionError("negative accepted: " + name)
    return len(mutations)


if __name__ == "__main__":
    data = validate_saved()
    print("PASS: two-session raw SQL/state replay; lost update/CAS/type/unknown/ABA/reset; source/artifact/UI binding; negatives=%d; read-only" % negatives(data))
