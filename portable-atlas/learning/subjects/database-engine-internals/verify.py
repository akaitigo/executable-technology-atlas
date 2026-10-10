#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""A result oracle independent of the runner, with pinned plan interpretation."""
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = ("experiment.py", "observe.py", "verify.py", "sources.json")


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def validate(raw):
    assert raw["subject"] == "database-engine-internals"
    runtime = raw["runtime"]
    assert runtime["engine"] == "SQLite" and runtime["database"] == ":memory:"
    assert runtime["sqlite_version"] == "3.51.0", "Different SQLite release: review plan oracle before new capture"
    assert runtime["sqlite_source_id"] and runtime["python_version"]
    setup = raw["setup"]
    expected_fixture = [[i, i % 16, "row-%03d" % i] for i in range(1, 257)]
    assert setup["fixture_count"] == 256 and setup["fixture_rows"] == expected_fixture
    assert setup["schema_sql"] == "CREATE TABLE samples (id INTEGER PRIMARY KEY, bucket INTEGER NOT NULL, label TEXT NOT NULL)"
    assert setup["index_sql"] == "CREATE INDEX samples_bucket_idx ON samples(bucket)"
    assert setup["insert_sql"] == "INSERT INTO samples(id, bucket, label) VALUES (?, ?, ?)"
    cases = raw["cases"]
    assert [x["id"] for x in cases] == ["no-index-equality", "indexed-equality", "indexed-expression"]
    # Mathematical result oracle, independent of experiment.py and SQL execution.
    expected = [[i, 7, "row-%03d" % i] for i in range(7, 257, 16)]
    expected_set = Counter(map(tuple, expected))
    for number, case in enumerate(cases):
        predicate = "bucket + 0 = ?" if number == 2 else "bucket = ?"
        assert case["query"] == "SELECT id, bucket, label FROM samples WHERE " + predicate + " ORDER BY id"
        assert case["parameters"] == [7]
        assert case["explain_query"] == "EXPLAIN QUERY PLAN " + case["query"]
        assert case["columns"] == ["id", "bucket", "label"]
        assert Counter(map(tuple, case["rows"])) == expected_set, "result multiset mismatch"
        assert case["rows"] == expected, "ORDER BY id drift"
        objects = [["table", "samples", setup["schema_sql"]]]
        if number:
            objects.insert(0, ["index", "samples_bucket_idx", setup["index_sql"]])
        assert case["schema_objects"] == objects
        assert case["plan"]["columns"] == ["id", "parent", "notused", "detail"]
        nodes = case["plan"]["rows"]
        assert len(nodes) == 1 and len(nodes[0]) == 4
        assert all(type(x) is int for x in nodes[0][:3])
        expected_detail = "SEARCH samples USING INDEX samples_bucket_idx (bucket=?)" if number == 1 else "SCAN samples"
        assert nodes[0][3] == expected_detail, "pinned SQLite plan mismatch"
    assert raw["scope"] == {
        "classification": "actual-sqlite-query-plan-and-results",
        "time_benchmark_performed": False, "speedup_claimed": False,
        "physical_page_trace": False, "wal_crash_recovery": False, "other_database_executed": False,
    }


def validate_saved(root=HERE):
    evidence = root / "evidence"
    raw_bytes = (evidence / "stdout.json").read_bytes()
    raw = json.loads(raw_bytes)
    report = json.loads((evidence / "run.json").read_text())
    validate(raw)
    assert report["status"] == "passed"
    assert report["process"] == {"attempts": 1, "retries": 0, "exit_code": 0}
    assert report["runtime"] == raw["runtime"]
    assert report["stdout_digest"] == digest(raw_bytes)
    assert report["stderr_digest"] == digest((evidence / "stderr.txt").read_bytes())
    assert set(report["source_digests"]) == set(INPUTS)
    for name in INPUTS:
        assert report["source_digests"][name] == digest((root / name).read_bytes()), name + " changed"
    js = "window.ENGINE_LESSON = " + json.dumps({"run": report, "raw": raw}, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + ";\n"
    assert (evidence / "data.js").read_text() == js, "UI replay diverges from evidence"
    return raw


def negatives(raw):
    mutations = {
        "missing-result": lambda x: x["cases"][1]["rows"].pop(),
        "duplicate-result": lambda x: x["cases"][1]["rows"].append(x["cases"][1]["rows"][0]),
        "invented-search": lambda x: x["cases"][0]["plan"]["rows"][0].__setitem__(3, "SEARCH samples"),
        "wrong-index": lambda x: x["cases"][1]["plan"]["rows"][0].__setitem__(3, "SEARCH samples USING INDEX other_idx (bucket=?)"),
        "expression-search-spoof": lambda x: x["cases"][2]["plan"]["rows"][0].__setitem__(3, x["cases"][1]["plan"]["rows"][0][3]),
        "missing-case": lambda x: x["cases"].pop(),
        "fixture-shrink": lambda x: x["setup"]["fixture_rows"].pop(),
        "speedup-overclaim": lambda x: x["scope"].__setitem__("speedup_claimed", True),
        "version-drift": lambda x: x["runtime"].__setitem__("sqlite_version", "3.52.0"),
    }
    for name, mutation in mutations.items():
        candidate = copy.deepcopy(raw)
        mutation(candidate)
        try:
            validate(candidate)
        except (AssertionError, KeyError, TypeError):
            continue
        raise AssertionError("Negative accepted: " + name)
    return len(mutations)


if __name__ == "__main__":
    raw = validate_saved()
    print("PASS: independent result multiset/order, schema/index, pinned raw plan, runtime/source/UI bindings; negative=%d" % negatives(raw))
