"""Independent hand rows and SQL oracle. Never imports service or runner."""
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Exact orders, exact outbox, request statuses: hand-authored, not producer output.
EXPECTED = {
    "atomic-normal": ([["a", "教材", 2]], [["a", "OrderCreated", '{"quantity": 2}']], [201]),
    "nonatomic-normal": ([["a", "教材", 2]], [["a", "OrderCreated", '{"quantity": 2}']], [201]),
    "atomic-second-failure": ([], [], [500]),
    "nonatomic-second-failure": ([["a", "教材", 2]], [], [500]),
    "quantity-one": ([["a", "教材", 1]], [["a", "OrderCreated", '{"quantity": 1}']], [201]),
    "quantity-hundred": ([["a", "教材", 100]], [["a", "OrderCreated", '{"quantity": 100}']], [201]),
    "quantity-zero": ([], [], [422]),
    "quantity-over": ([], [], [422]),
    "quantity-bool": ([], [], [422]),
    "blank-name": ([], [], [422]),
    "duplicate-id": ([["a", "教材", 2]], [["a", "OrderCreated", '{"quantity": 2}']], [201, 409]),
    "failure-then-next-request": ([["b", "教材", 2]], [["b", "OrderCreated", '{"quantity": 2}']], [500, 201]),
}


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def safe_folder(value):
    assert re.fullmatch(r"observations/[0-9TZ]+", value), "unsafe path"
    return ROOT / value


def oracle(folder):
    obs = json.loads((folder / "observation.json").read_text())
    assert {r["id"] for r in obs["scenarios"]} == set(EXPECTED)
    rows = []
    for row in obs["scenarios"]:
        case = folder / row["id"]
        db = sqlite3.connect((case / "service.sqlite").as_uri() + "?mode=ro&immutable=1", uri=True)
        try:
            db.execute("PRAGMA query_only=ON")
            orders = [list(x) for x in db.execute("SELECT id,name,quantity FROM orders ORDER BY id")]
            events = [list(x) for x in db.execute("SELECT order_id,event,payload FROM outbox ORDER BY order_id")]
            integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
            foreign = db.execute("PRAGMA foreign_key_check").fetchall()
        finally:
            db.close()
        trace = json.loads((case / "trace.json").read_text())
        statuses = [x["status"] for x in trace if x["event"] in ("response", "validation-rejected")]
        expected = EXPECTED[row["id"]]
        actual = (orders, events, statuses)
        rows.append({"id": row["id"], "expected": list(expected), "actual": list(actual), "match": actual == expected and integrity == "ok" and not foreign, "order_without_outbox": sorted(set(x[0] for x in orders) - set(x[0] for x in events)), "integrity": integrity})
    return {"execution_id": obs["execution_id"], "method": "independent-hand-rows/read-only-SQL", "rows": rows}


def check():
    folder = safe_folder(json.loads((ROOT / "current.json").read_text())["directory"])
    obs = json.loads((folder / "observation.json").read_text())
    report = oracle(folder)
    assert all(r["match"] for r in report["rows"]), report
    assert report == json.loads((folder / "oracle.json").read_text())
    for row in obs["scenarios"]:
        case = folder / row["id"]
        command = json.loads((case / "command.json").read_text())
        assert command["exit_code"] == 0 and not command["stderr"]
        assert command["started_at"] <= command["completed_at"]
        for key in ("stdin", "stdout", "stderr"):
            assert sha(command[key].encode()) == command[key + "_digest"]
        assert json.loads(command["stdin"]) == row["input"] == json.loads((case / "input.json").read_text())
        trace = [json.loads(x) for x in command["stdout"].splitlines()]
        assert trace == row["trace"] == json.loads((case / "trace.json").read_text())
        events = [x["event"] for x in trace]
        opened = events.count("connection-opened")
        assert opened == events.count("connection-closed")
        assert all(x["probe"] == "ProgrammingError" for x in trace if x["event"] == "connection-closed")
        assert all(not x["active"] for x in trace if x["event"] == "transaction-after-request")
        sql = [x["sql"] for x in trace if x["event"] == "sql"]
        if row["id"] in ("quantity-zero", "quantity-over", "quantity-bool", "blank-name"):
            assert opened == 0 and sql == []
        if row["id"] in ("atomic-second-failure", "failure-then-next-request", "duplicate-id"):
            assert "ROLLBACK" in sql and "BEGIN IMMEDIATE" in sql
        if row["id"] == "nonatomic-second-failure":
            assert not any(s in ("BEGIN IMMEDIATE", "ROLLBACK", "COMMIT") for s in sql)
        if row["id"] == "failure-then-next-request":
            closes = [i for i, e in enumerate(events) if e == "connection-closed"]
            opens = [i for i, e in enumerate(events) if e == "connection-opened"]
            assert closes[0] < opens[1]
    index = json.loads((folder / "artifact-index.json").read_text())
    files = {p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()}
    assert files == set(index) | {"artifact-index.json"}
    for name, meta in index.items():
        raw = (folder / name).read_bytes()
        assert meta == {"digest": sha(raw), "size": len(raw)}, name
    for name, value in obs["source_bindings"].items():
        assert sha((ROOT / name).read_bytes()) == value, "source drift: " + name
    sources = json.loads((ROOT / "sources.json").read_text())
    coverage = json.loads((ROOT / "coverage.json").read_text())
    assert len(coverage["next_experiments"]) in range(2, 5)
    assert len(coverage["areas"]) >= 8
    assert all(a["source"] in sources for a in coverage["areas"])
    for name in ("README.md", "index.html"):
        text = (ROOT / name).read_text()
        for term in ("前提", "主要概念", "実務判断", "限界", "原典", "次の実験"):
            assert term in text, (name, term)
        links = re.findall(r'\]\(([^)]+)\)', text) if name.endswith("md") else re.findall(r'href="([^"]+)"', text)
        for link in links:
            if not link.startswith(("https:", "#")):
                assert (ROOT / link.split("#")[0]).exists(), link
    oracle_command = json.loads((folder / "oracle-command.json").read_text())
    assert oracle_command["exit_code"] == 0 and json.loads(oracle_command["stdout"]) == report
    for key in ("stdout", "stderr"):
        assert sha(oracle_command[key].encode()) == oracle_command[key + "_digest"]
    print(json.dumps({"status": "passed", "cases": len(EXPECTED), "oracle": "SQL + hand rows", "source_binding": "passed", "roadmap_links": "passed", "default_mode": "read-only"}, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--oracle":
        print(json.dumps(oracle(safe_folder(sys.argv[2])), ensure_ascii=False))
    else:
        assert len(sys.argv) == 1, "unsupported checker option"
        check()
