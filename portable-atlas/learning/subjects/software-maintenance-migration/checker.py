"""Independent hand mapping and read-only SQL. No migrator/runner imports."""
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
V1_SQL = 'CREATE TABLE "orders" (id TEXT PRIMARY KEY, amount_text TEXT NOT NULL, state TEXT NOT NULL)'
V2_SQL = 'CREATE TABLE "orders" (id TEXT PRIMARY KEY, amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0), state_code INTEGER NOT NULL)'
V1_ROWS = [["a", "12.30", "new"], ["b", "0.00", "paid"], ["c", "1.05", "new"]]
V2_ROWS = [["a", 1230, 10], ["b", 0, 20], ["c", 105, 10]]
# (before version/rows, each after version/rows/outcome/exit/reason). All fixed by hand.
EXPECTED = {
    "normal-up": (1, V1_ROWS, [(2, V2_ROWS, "migrated", 0, None)]),
    "roundtrip": (1, V1_ROWS, [(2, V2_ROWS, "migrated", 0, None), (1, V1_ROWS, "migrated", 0, None)]),
    "empty-roundtrip": (1, [], [(2, [], "migrated", 0, None), (1, [], "migrated", 0, None)]),
    "zero-boundary": (1, [["a", "0.00", "new"]], [(2, [["a", 0, 10]], "migrated", 0, None)]),
    "lossy-refused": (1, [["a", "1.005", "new"]], [(1, [["a", "1.005", "new"]], "refused", 2, "noncanonical-or-lossy-amount:1.005")]),
    "lossy-forced-roundtrip": (1, [["a", "1.005", "new"]], [(2, [["a", 100, 10]], "migrated", 0, None), (1, [["a", "1.00", "new"]], "migrated", 0, None)]),
    "unknown-state-refused": (1, [["a", "12.30", "refunded"]], [(1, [["a", "12.30", "refunded"]], "refused", 2, "unknown-state:refunded")]),
    "noncanonical-refused": (1, [["a", "01.20", "new"]], [(1, [["a", "01.20", "new"]], "refused", 2, "noncanonical-or-lossy-amount:01.20")]),
    "overflow-refused": (1, [["a", "92233720368547758.08", "new"]], [(1, [["a", "92233720368547758.08", "new"]], "refused", 2, "amount-out-of-int64-range")]),
    "failure-after-copy": (1, V1_ROWS, [(1, V1_ROWS, "rolled-back", 3, "injected-after-copy")]),
    "failure-after-drop": (1, V1_ROWS, [(1, V1_ROWS, "rolled-back", 3, "injected-after-drop")]),
    "down-unknown-refused": (2, [["a", 1230, 30]], [(2, [["a", 1230, 30]], "refused", 2, "unknown-state-code:30")]),
    "unsupported-version": (99, V1_ROWS, [(99, V1_ROWS, "refused", 2, "unsupported-source-version:99")]),
}
HAND_MAPPING = [
    {"v1": ["a", "12.30", "new"], "v2": ["a", 1230, 10]},
    {"v1": ["b", "0.00", "paid"], "v2": ["b", 0, 20]},
    {"v1": ["c", "1.05", "new"], "v2": ["c", 105, 10]},
]


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def safe_folder(value):
    assert re.fullmatch(r"observations/[0-9TZ]+", value), "unsafe path"
    return ROOT / value


def snapshot(path):
    db = sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)
    try:
        db.execute("PRAGMA query_only=ON")
        version = db.execute("PRAGMA user_version").fetchone()[0]
        schema = [list(x) for x in db.execute("SELECT type,name,tbl_name,sql FROM sqlite_schema ORDER BY type,name")]
        columns = [list(x) for x in db.execute("PRAGMA table_info(orders)")]
        rows = [list(x) for x in db.execute("SELECT * FROM orders ORDER BY id")]
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        db.close()
    schema_state = {"version": version, "schema": schema, "columns": columns}
    return {**schema_state, "rows": rows, "row_hash": sha(encoded(rows)), "schema_hash": sha(encoded(schema_state)), "database_digest": sha(path.read_bytes()), "integrity": integrity}


def matches(state, version, rows):
    sql = V2_SQL if version == 2 else V1_SQL
    columns = [[0, "id", "TEXT", 0, None, 1], [1, "amount_cents" if version == 2 else "amount_text", "INTEGER" if version == 2 else "TEXT", 1, None, 0], [2, "state_code" if version == 2 else "state", "INTEGER" if version == 2 else "TEXT", 1, None, 0]]
    schema = [["index", "sqlite_autoindex_orders_1", "orders", None], ["table", "orders", "orders", sql]]
    return state["version"] == version and state["rows"] == rows and state["schema"] == schema and state["columns"] == columns and state["integrity"] == "ok"


def unchanged(before, after):
    return before["row_hash"] == after["row_hash"] and before["schema_hash"] == after["schema_hash"]


def oracle(folder):
    obs = json.loads((folder / "observation.json").read_text())
    assert {r["id"] for r in obs["runs"]} == set(EXPECTED) and len(obs["runs"]) == len(EXPECTED)
    report = []
    for run in obs["runs"]:
        case = folder / run["id"]
        version, rows, steps = EXPECTED[run["id"]]
        before = snapshot(case / "before.sqlite")
        afters = []
        previous = before
        for i, (v, mapped, outcome, exit_code, reason) in enumerate(steps, 1):
            state = snapshot(case / f"after-{i}.sqlite")
            trace = json.loads((case / f"step-{i}-trace.json").read_text())
            terminal = [x for x in trace if x["event"] in ("migrated", "refused", "rolled-back")]
            command = json.loads((case / f"step-{i}-command.json").read_text())
            terminal_match = len(terminal) == 1 and terminal[0]["event"] == outcome and terminal[0].get("reason") == reason and command["exit_code"] == exit_code
            afters.append({"step": i, "state": state, "expected_version": v, "expected_rows": mapped, "expected_outcome": outcome, "expected_exit": exit_code, "matches_expected": matches(state, v, mapped) and terminal_match, "row_schema_unchanged": unchanged(previous, state), "database_bytes_unchanged": previous["database_digest"] == state["database_digest"], "outcome": terminal[0] if len(terminal) == 1 else terminal})
            previous = state
        roundtrip = len(steps) == 2
        report.append({"id": run["id"], "before": before, "before_matches_expected": matches(before, version, rows), "steps": afters, "roundtrip_executed": roundtrip, "roundtrip_restores_rows_and_schema": unchanged(before, previous) if roundtrip else None, "mapping_preserves_information": run["id"] != "lossy-forced-roundtrip", "final_matches_working_db": previous == snapshot(case / "working.sqlite")})
    return {"execution_id": obs["execution_id"], "method": "independent fixed hand mapping + direct read-only SQLite schema/row queries", "hand_mapping": HAND_MAPPING, "runs": report}


def check():
    folder = safe_folder(json.loads((ROOT / "current.json").read_text())["directory"])
    obs = json.loads((folder / "observation.json").read_text())
    report = oracle(folder)
    assert all(r["before_matches_expected"] and r["final_matches_working_db"] and all(s["matches_expected"] for s in r["steps"]) for r in report["runs"])
    assert report == json.loads((folder / "oracle.json").read_text())
    by_id = {r["id"]: r for r in report["runs"]}
    assert by_id["roundtrip"]["roundtrip_restores_rows_and_schema"] is True
    assert by_id["empty-roundtrip"]["roundtrip_restores_rows_and_schema"] is True
    assert by_id["lossy-forced-roundtrip"]["roundtrip_restores_rows_and_schema"] is False
    for run in obs["runs"]:
        case = folder / run["id"]
        assert json.loads((case / "input.json").read_text()) == {k: run[k] for k in ("source_version", "seed_rows", "steps")}
        assert len(run["steps"]) == len(EXPECTED[run["id"]][2])
        for i, step in enumerate(run["steps"], 1):
            command = json.loads((case / f"step-{i}-command.json").read_text())
            assert not command["stderr"] and command["started_at"] <= command["completed_at"]
            for stream in ("stdin", "stdout", "stderr"):
                assert sha(command[stream].encode()) == command[stream + "_digest"]
            assert json.loads(command["stdin"]) == step
            trace = [json.loads(x) for x in command["stdout"].splitlines()]
            assert trace == json.loads((case / f"step-{i}-trace.json").read_text())
            assert any(x["event"] == "connection-closed" and x["probe"] == "ProgrammingError" for x in trace)
            assert all(not x["active"] for x in trace if x["event"] == "transaction-after-step")
            actual = by_id[run["id"]]["steps"][i - 1]
            sql = [x["sql"] for x in trace if x["event"] == "sql"]
            outcome = actual["expected_outcome"]
            if outcome == "refused":
                assert "BEGIN IMMEDIATE" not in sql and actual["row_schema_unchanged"]
            else:
                assert "BEGIN IMMEDIATE" in sql
                assert any(s.startswith('CREATE TABLE "orders_staged"') for s in sql)
                if outcome == "rolled-back":
                    assert "ROLLBACK" in sql and "COMMIT" not in sql and actual["row_schema_unchanged"]
                else:
                    assert "DROP TABLE orders" in sql and "COMMIT" in sql
            if run["id"] == "failure-after-drop":
                assert sql.index("DROP TABLE orders") < sql.index("ROLLBACK")
    index = json.loads((folder / "artifact-index.json").read_text())
    files = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    assert files == set(index) | {"artifact-index.json"}
    for name, meta in index.items():
        raw = (folder / name).read_bytes()
        assert meta == {"digest": sha(raw), "size": len(raw)}, name
    for name, digest in obs["source_bindings"].items():
        assert sha((ROOT / name).read_bytes()) == digest, "source drift: " + name
    sources = json.loads((ROOT / "sources.json").read_text())
    coverage = json.loads((ROOT / "coverage.json").read_text())
    assert 2 <= len(coverage["next_experiments"]) <= 4 and len(coverage["areas"]) >= 10
    assert all(x["source"] in sources for x in coverage["areas"])
    assert all(s in sources for x in coverage["next_experiments"] for s in x["source"])
    for name in ("README.md", "index.html"):
        text = (ROOT / name).read_text()
        assert all(term in text for term in ("前提", "主要概念", "実務判断", "限界", "原典", "次の実験"))
        links = re.findall(r'\]\(([^)]+)\)', text) if name.endswith("md") else re.findall(r'href="([^"]+)"', text)
        for link in links:
            if not link.startswith(("https:", "#")):
                assert (ROOT / link.split("#")[0]).exists(), link
    command = json.loads((folder / "oracle-command.json").read_text())
    assert command["exit_code"] == 0 and json.loads(command["stdout"]) == report
    assert all(sha(command[k].encode()) == command[k + "_digest"] for k in ("stdout", "stderr"))
    print(json.dumps({"status": "passed", "cases": len(EXPECTED), "steps": sum(len(x[2]) for x in EXPECTED.values()), "row_schema_hashes": "passed", "reversible_exact_mapping": "passed", "lossy_counterexample": "detected", "source_binding": "passed", "roadmap_local_links": "passed", "default": "read-only"}, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--oracle":
        print(json.dumps(oracle(safe_folder(sys.argv[2])), ensure_ascii=False))
    else:
        assert len(sys.argv) == 1, "unsupported checker option"
        check()
