#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Independently verify the saved SQLite observation and negative mutations."""

import copy
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha256(path):
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def by_id(items):
    return {item["id"]: item for item in items}


def validate_payload(payload):
    execution = payload["execution"]
    assert execution["engine"] == "SQLite"
    assert execution["database"] == ":memory:"
    assert execution["sqlite_version"] == "3.51.0"
    assert execution["python_version"] == "3.9.6"
    assert execution["sqlite_source_id"] == (
        "2025-06-12 13:14:41 "
        "f0ca7bba1c5e232e5d279fad6338121ab55af0c8c68c84cdfb18ba5114dcaapl"
    )
    assert execution["foreign_keys_pragma"] == 1
    assert execution["attempts"] == 1 and execution["retries"] == 0

    queries = by_id(payload["queries"])
    assert set(queries) == {
        "null.equals-null",
        "null.is-null",
        "null.truth-values",
        "join.inner",
        "join.left",
        "join.left-where",
        "join.left-on",
    }
    assert queries["null.equals-null"]["rows"] == []
    assert queries["null.is-null"]["rows"] == [{"id": 2, "label": "beta"}]
    assert queries["null.truth-values"]["rows"] == [{
        "null_eq_null": None,
        "null_is_null": 1,
        "unknown_or_true": 1,
        "unknown_and_false": 0,
    }]
    assert queries["join.inner"]["rows"] == [
        {"row_id": 1, "label": "alpha", "event_id": 101, "kind": "keep"},
        {"row_id": 1, "label": "alpha", "event_id": 102, "kind": "review"},
        {"row_id": 2, "label": "beta", "event_id": 103, "kind": "review"},
    ]
    assert queries["join.left"]["rows"][-1] == {
        "row_id": 3, "label": "gamma", "event_id": None, "kind": None
    }
    assert queries["join.left-where"]["rows"] == [
        {"row_id": 1, "label": "alpha", "event_id": 101, "kind": "keep"}
    ]
    assert queries["join.left-on"]["rows"] == [
        {"row_id": 1, "label": "alpha", "event_id": 101, "kind": "keep"},
        {"row_id": 2, "label": "beta", "event_id": None, "kind": None},
        {"row_id": 3, "label": "gamma", "event_id": None, "kind": None},
    ]

    constraints = payload["constraints"]
    assert constraints["foreign_keys_pragma"] == 1
    assert constraints["unique_null_rows"] == 2
    cases = by_id(constraints["cases"])
    assert set(cases) == {
        "constraint.not-null",
        "constraint.unique-non-null",
        "constraint.foreign-key",
    }
    for case in cases.values():
        assert case["accepted"] is False
        assert case["error_type"] == "IntegrityError"
        assert case["message"]
    assert cases["constraint.not-null"]["message"].startswith("NOT NULL constraint failed:")
    assert cases["constraint.unique-non-null"]["message"].startswith("UNIQUE constraint failed:")
    assert cases["constraint.foreign-key"]["message"] == "FOREIGN KEY constraint failed"

    assert payload["classification"]["actual"].startswith("Python stdlib sqlite3")
    assert "PostgreSQL execution" in payload["classification"]["not_observed"]


def validate_sources():
    document = json.loads((HERE / "sources.json").read_text())
    assert document["copyright_policy"]["third_party_body_saved"] is False
    assert len(document["sources"]) == 4
    for source in document["sources"]:
        assert source["publisher"] == "SQLite"
        assert source["url"].startswith("https://sqlite.org/")
        assert source["digest_scope"] == "canonical-url"
        assert source["url_sha256"] == "sha256:" + hashlib.sha256(
            source["url"].encode()
        ).hexdigest()
        assert source["locators"] and source["supports"]
        assert "body" not in source and "content" not in source


def validate_document(document, raw):
    assert document["subject"] == "relational-database-sql"
    assert document["status"] == "passed"
    assert document["process"] == {"exit_code": 0, "attempts": 1, "retries": 0}
    assert document["raw_stdout_sha256"] == "sha256:" + hashlib.sha256(
        (json.dumps(raw, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    ).hexdigest()
    validate_payload(raw)
    validate_sources()
    for name, digest in document["source_digests"].items():
        assert sha256(HERE / name) == digest, f"source digest mismatch: {name}"


def reject_mutations(raw):
    mutations = []

    candidate = copy.deepcopy(raw)
    by_id(candidate["queries"])["null.equals-null"]["rows"] = [{"id": 2, "label": "beta"}]
    mutations.append(("invented-equals-null-row", candidate))

    candidate = copy.deepcopy(raw)
    by_id(candidate["queries"])["null.is-null"]["rows"] = []
    mutations.append(("missing-is-null-row", candidate))

    candidate = copy.deepcopy(raw)
    by_id(candidate["queries"])["join.left-where"]["rows"].append(
        {"row_id": 3, "label": "gamma", "event_id": None, "kind": None}
    )
    mutations.append(("where-invented-unmatched-row", candidate))

    candidate = copy.deepcopy(raw)
    by_id(candidate["queries"])["join.left-on"]["rows"].pop()
    mutations.append(("on-dropped-unmatched-row", candidate))

    candidate = copy.deepcopy(raw)
    candidate["constraints"]["foreign_keys_pragma"] = 0
    mutations.append(("foreign-keys-disabled", candidate))

    candidate = copy.deepcopy(raw)
    by_id(candidate["constraints"]["cases"])["constraint.not-null"]["accepted"] = True
    mutations.append(("not-null-accepted", candidate))

    candidate = copy.deepcopy(raw)
    candidate["execution"]["engine"] = "PostgreSQL"
    mutations.append(("engine-overclaim", candidate))

    candidate = copy.deepcopy(raw)
    candidate["queries"].pop()
    mutations.append(("missing-query", candidate))

    for name, candidate in mutations:
        try:
            validate_payload(candidate)
        except (AssertionError, KeyError, TypeError):
            continue
        raise AssertionError(f"negative mutation accepted: {name}")
    return len(mutations)


def main():
    evidence = HERE / "evidence"
    document = json.loads((evidence / "run.json").read_text())
    raw_bytes = (evidence / "raw-results.json").read_bytes()
    raw = json.loads(raw_bytes)
    assert document["raw_stdout_sha256"] == "sha256:" + hashlib.sha256(raw_bytes).hexdigest()
    validate_document(document, raw)
    negatives = reject_mutations(raw)
    print(
        "Verification: NULL/3VL, JOIN retention, constraints, runtime/source binding "
        f"PASS; negatives={negatives}"
    )


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, KeyError, TypeError, ValueError) as error:
        print(f"Verification failed: {error}", file=sys.stderr)
        raise
