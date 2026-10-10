"""Independent fixed rows, direct SQL and AST imports; no producer import."""
import ast
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def created(row):
    return {"status": 201, "body": row}


INVALID = {"status": 422, "error": "invalid-order"}
CONFLICT = {"status": 409, "error": "duplicate-order"}
UNAVAILABLE = {"status": 503, "error": "storage-unavailable"}
LEAKED = {"status": 500, "error": "untranslated-storage-error"}
# Exact fixed hand expectations. Not computed from requests or imported business rules.
PORT = {
    "normal": ([["a", "book", 2, 240]], [created(["a", "book", 2, 240])]),
    "quantity-one": ([["a", "book", 1, 120]], [created(["a", "book", 1, 120])]),
    "quantity-hundred": ([["a", "book", 100, 12000]], [created(["a", "book", 100, 12000])]),
    "quantity-zero": ([], [INVALID]),
    "quantity-over": ([], [INVALID]),
    "quantity-bool": ([], [INVALID]),
    "spaces": ([["a", "book", 2, 240]], [created(["a", "book", 2, 240])]),
    "blank-sku": ([], [INVALID]),
    "missing-id": ([], [INVALID]),
    "duplicate-id": ([["a", "book", 2, 240]], [created(["a", "book", 2, 240]), CONFLICT]),
    "unavailable": ([], [UNAVAILABLE]),
    "invalid-unavailable": ([], [INVALID]),
}
TIED_MEMORY = {
    **PORT,
    "quantity-bool": ([["a", "book", 1, 120]], [created(["a", "book", 1, 120])]),
    "duplicate-id": ([["a", "book", 2, 240]], [created(["a", "book", 2, 240]), LEAKED]),
    "unavailable": ([], [LEAKED]),
}
TIED_SQLITE = {
    **PORT,
    "normal": ([["a", "book", 2, 200]], [created(["a", "book", 2, 200])]),
    "quantity-one": ([["a", "book", 1, 100]], [created(["a", "book", 1, 100])]),
    "quantity-hundred": ([["a", "book", 100, 10000]], [created(["a", "book", 100, 10000])]),
    "quantity-bool": ([["a", "book", 1, 100]], [created(["a", "book", 1, 100])]),
    "spaces": ([[" a ", " book ", 2, 200]], [created([" a ", " book ", 2, 200])]),
    "duplicate-id": ([["a", "book", 3, 300]], [created(["a", "book", 2, 200]), created(["a", "book", 3, 300])]),
    "unavailable": ([], [LEAKED]),
}


def sha(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def safe_folder(value):
    assert re.fullmatch(r"observations/[0-9TZ]+", value), "unsafe observation path"
    return ROOT / value


def dependency_graph():
    edges = []
    files = ["ports.py", "domain.py", "adapters.py", "bad.py", "worker.py"]
    for name in files:
        tree = ast.parse((ROOT / name).read_text())
        for node in ast.walk(tree):
            modules = [x.name for x in node.names] if isinstance(node, ast.Import) else [node.module] if isinstance(node, ast.ImportFrom) else []
            for module in modules:
                edges.append({"from": name, "to": module, "line": node.lineno})
    return {"method": "actual Python AST import statements; arrows are source dependency, not runtime calls", "edges": sorted(edges, key=lambda x: (x["from"], x["line"], x["to"]))}


def oracle(folder):
    obs = json.loads((folder / "observation.json").read_text())
    denominator = {f"{variant}-{storage}-{scenario}" for variant in ("port", "tied") for storage in ("memory", "sqlite") for scenario in PORT}
    assert {r["id"] for r in obs["runs"]} == denominator and len(obs["runs"]) == len(denominator)
    results = []
    for run in obs["runs"]:
        case = folder / run["id"]
        if run["storage"] == "sqlite":
            db = sqlite3.connect((case / "orders.sqlite").as_uri() + "?mode=ro&immutable=1", uri=True)
            try:
                db.execute("PRAGMA query_only=ON")
                rows = [list(x) for x in db.execute("SELECT id,sku,quantity,total FROM orders ORDER BY id")]
                integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
            finally:
                db.close()
        else:
            rows = json.loads((case / "memory-final.json").read_text())
            integrity = "not-applicable-memory"
        trace = json.loads((case / "trace.json").read_text())
        responses = [{k: v for k, v in x.items() if k not in ("event", "index")} for x in trace if x["event"] == "response"]
        actual = (rows, responses)
        fixed = PORT if run["variant"] == "port" else TIED_MEMORY if run["storage"] == "memory" else TIED_SQLITE
        expected = fixed[run["scenario"]]
        results.append({"id": run["id"], "variant": run["variant"], "storage": run["storage"], "scenario": run["scenario"], "actual": list(actual), "expected": list(expected), "matches_fixed_expected": actual == expected and integrity in ("ok", "not-applicable-memory"), "contract_conforms": actual == PORT[run["scenario"]], "integrity": integrity})
    pairs = []
    by_id = {r["id"]: r for r in results}
    for variant in ("port", "tied"):
        for scenario in PORT:
            memory = by_id[f"{variant}-memory-{scenario}"]
            sql = by_id[f"{variant}-sqlite-{scenario}"]
            pairs.append({"variant": variant, "scenario": scenario, "same_observable_result": memory["actual"] == sql["actual"], "both_conform": memory["contract_conforms"] and sql["contract_conforms"]})
    return {"execution_id": obs["execution_id"], "method": "independent-fixed-hand-rows; SQLite read-only SQL; memory exported raw snapshot", "runs": results, "pairs": pairs, "dependency_graph": dependency_graph()}


def check():
    folder = safe_folder(json.loads((ROOT / "current.json").read_text())["directory"])
    obs = json.loads((folder / "observation.json").read_text())
    report = oracle(folder)
    assert all(r["matches_fixed_expected"] for r in report["runs"])
    assert all(p["same_observable_result"] and p["both_conform"] for p in report["pairs"] if p["variant"] == "port")
    assert not next(p for p in report["pairs"] if p["variant"] == "tied" and p["scenario"] == "normal")["same_observable_result"]
    assert not next(p for p in report["pairs"] if p["variant"] == "tied" and p["scenario"] == "unavailable")["both_conform"]
    assert report == json.loads((folder / "oracle.json").read_text())
    for run in obs["runs"]:
        case = folder / run["id"]
        command = json.loads((case / "command.json").read_text())
        assert command["exit_code"] == 0 and not command["stderr"]
        assert command["started_at"] <= command["completed_at"]
        for key in ("stdin", "stdout", "stderr"):
            assert sha(command[key].encode()) == command[key + "_digest"]
        assert json.loads(command["stdin"]) == run["input"] == json.loads((case / "input.json").read_text())
        trace = [json.loads(x) for x in command["stdout"].splitlines()]
        assert trace == json.loads((case / "trace.json").read_text())
        actual = next(r for r in report["runs"] if r["id"] == run["id"])["actual"][0]
        assert next(x for x in trace if x["event"] == "final-state")["rows"] == actual
        assert sum(x["event"] == "adapter-closed" for x in trace) == 1
        if run["variant"] == "port" and run["scenario"] in ("quantity-zero", "quantity-over", "quantity-bool", "blank-sku", "missing-id", "invalid-unavailable"):
            assert not any(x["event"] in ("port-add", "sql") for x in trace)
        if run["variant"] == "port" and run["scenario"] == "unavailable":
            chain = next(x["chain"] for x in trace if x["event"] == "translated-exception")
            assert chain == ["DependencyUnavailable", "StoreUnavailable", "OSError" if run["storage"] == "memory" else "ProgrammingError"]
    edges = report["dependency_graph"]["edges"]
    assert {x["to"] for x in edges if x["from"] == "domain.py"} == {"ports"}
    assert {"adapters", "sqlite3"} <= {x["to"] for x in edges if x["from"] == "bad.py"}
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
    print(json.dumps({"status": "passed", "runs": 48, "port_pairs_conform": 12, "source_binding": "passed", "raw_dependency_graph": "AST", "roadmap_local_links": "passed", "default": "read-only"}, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--oracle":
        print(json.dumps(oracle(safe_folder(sys.argv[2])), ensure_ascii=False))
    else:
        assert len(sys.argv) == 1, "unsupported checker option"
        check()
