#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Read-only checker: character-walking full scan, independent of the indexer."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUTS = ("indexer.py", "experiment.py", "observe.py", "verify.py", "sources.json", "index.html", "app.js", "style.css",
          "README.md", "COVERAGE.md", "test_contract.py", "skills/atlas-information-retrieval-search/SKILL.md")
BASE = {"d1": "Blue green note", "d2": "Blue red memo", "d3": "Green gold note", "d4": "Red blue blue log", "d5": ""}


def digest(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def object_hash(value):
    return digest(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode())


def scan_tokens(text):
    # No regex, indexer import or inverted-index access.
    words, buffer = [], ""
    for char in text.lower() + " ":
        if "a" <= char <= "z" or "0" <= char <= "9":
            buffer += char
        elif buffer:
            words.append(buffer)
            buffer = ""
    return words


def fullscan(documents, terms, operator):
    if not terms:
        return []
    result = []
    for doc_id, text in sorted(documents.items()):
        present = set(scan_tokens(text))
        condition = all(term in present for term in terms) if operator == "AND" else any(term in present for term in terms)
        if condition:
            result.append(doc_id)
    return result


def validate(raw):
    assert raw["subject"] == "information-retrieval-search" and raw["runtime"]["python_version"]
    expected_current = dict(BASE, d1="Gold green note")
    assert raw["input"] == {"initial_documents": BASE, "update": {"doc_id": "d1", "text": "Gold green note"},
        "tokenizer": "lowercase then ASCII [a-z0-9]+ runs; duplicate terms collapsed per query",
        "operators": ["AND", "OR"], "schedule": "build -> query -> update without rebuild -> query -> rebuild -> query"}
    assert [snapshot["id"] for snapshot in raw["snapshots"]] == ["initial", "stale", "rebuilt"]
    snapshots = {snapshot["id"]: snapshot for snapshot in raw["snapshots"]}
    for stage, snapshot in snapshots.items():
        docs = BASE if stage == "initial" else expected_current
        built_docs = expected_current if stage == "rebuilt" else BASE
        assert snapshot["documents"] == docs and snapshot["indexed_documents"] == built_docs
        assert snapshot["corpus_hash"] == object_hash(docs)
        index = snapshot["index"]
        assert index["built_from_corpus_hash"] == object_hash(built_docs)
        expected_postings = {}
        for doc_id, text in sorted(built_docs.items()):
            for term in set(scan_tokens(text)):
                expected_postings.setdefault(term, []).append(doc_id)
        assert index["postings"] == expected_postings
        assert index["postings_hash"] == object_hash(expected_postings)
        assert snapshot["document_tokens"] == {key: scan_tokens(text) for key, text in sorted(docs.items())}
    assert snapshots["stale"]["index"] == snapshots["initial"]["index"]
    assert snapshots["stale"]["corpus_hash"] != snapshots["stale"]["index"]["built_from_corpus_hash"]
    specs = [
        ("initial.and", "blue green", "AND"), ("initial.or", "blue green", "OR"),
        ("initial.case-punctuation", "BLUE, Green!", "AND"), ("initial.duplicate", "blue blue", "AND"),
        ("initial.empty", "  ...  ", "OR"), ("initial.unknown", "violet", "AND"),
        ("initial.unknown-and", "blue violet", "AND"), ("initial.unknown-or", "blue violet", "OR"),
        ("initial.ascii-boundary", "blue-green 東京", "AND"),
        ("stale.removed-blue", "blue green", "AND"), ("stale.added-gold", "gold green", "AND"),
        ("rebuilt.removed-blue", "blue green", "AND"), ("rebuilt.added-gold", "gold green", "AND"),
    ]
    assert len(raw["queries"]) == len(specs)
    verdicts = []
    for query, (case_id, text, mode) in zip(raw["queries"], specs):
        assert (query["id"], query["query"], query["operator"]) == (case_id, text, mode)
        stage = case_id.split(".")[0]
        assert query["stage"] == stage
        snapshot = snapshots[stage]
        terms = list(dict.fromkeys(scan_tokens(text)))
        assert query["terms"] == terms
        assert query["status"] == ("ok" if terms else "empty-query")
        assert len(query["posting_steps"]) == len(terms)
        # Replay actual posting steps and independently derive final index IDs by scanning indexed source docs.
        accumulator = None
        for step, term in zip(query["posting_steps"], terms):
            posting = snapshot["index"]["postings"].get(term, [])
            assert step["term"] == term and step["posting"] == posting
            assert step["before"] == (None if accumulator is None else sorted(accumulator))
            accumulator = set(posting) if accumulator is None else (accumulator & set(posting) if mode == "AND" else accumulator | set(posting))
            assert step["after"] == sorted(accumulator)
        actual = fullscan(snapshot["indexed_documents"], terms, mode)
        assert query["doc_ids"] == actual
        assert query["rows"] == [{"id": doc_id, "text": snapshot["documents"][doc_id]} for doc_id in actual]
        reference = fullscan(snapshot["documents"], terms, mode)
        extra = sorted(set(actual)-set(reference))
        missing = sorted(set(reference)-set(actual))
        expected_extra = ["d1"] if case_id == "stale.removed-blue" else []
        expected_missing = ["d1"] if case_id == "stale.added-gold" else []
        assert extra == expected_extra and missing == expected_missing
        verdicts.append({"id": case_id, "index_ids": actual, "fullscan_ids": reference,
                         "stale_hits": extra, "missing_hits": missing,
                         "classification": "expected-anomaly" if extra or missing else "match"})
    assert raw["scope"] == {"actual": "executed Python stdlib inverted index with synthetic documents",
        "ranked_retrieval": False, "bm25": False, "semantic_embedding": False, "product_engine": False,
        "performance_benchmark": False, "unicode_morphology": False}
    return verdicts


def validate_saved(root=HERE):
    folder = root / "evidence"
    inventory = json.loads((folder / "artifacts.json").read_text())
    assert set(inventory) == {"stdout.json", "stderr.txt", "run.json", "verification.json", "data.js"}
    assert {path.name for path in folder.iterdir()} == set(inventory) | {"artifacts.json"}
    for name, binding in inventory.items():
        content = (folder / name).read_bytes()
        assert binding == {"digest": digest(content), "bytes": len(content)}, "artifact mismatch: " + name
    raw = json.loads((folder / "stdout.json").read_text())
    report = json.loads((folder / "run.json").read_text())
    verdicts = validate(raw)
    assert json.loads((folder / "verification.json").read_text()) == {"oracle": "independent-character-walk-fullscan", "verdicts": verdicts}
    assert report["runtime"] == raw["runtime"] and report["input"] == raw["input"]
    assert report["status"] == "passed-with-demonstrated-anomalies"
    assert report["process"] == {"attempts": 1, "retries": 0, "exit_code": 0}
    assert set(report["source_digests"]) == set(INPUTS)
    for name in INPUTS:
        assert report["source_digests"][name] == digest((root / name).read_bytes()), "stale source: " + name
    assert report["stdout_digest"] == digest((folder / "stdout.json").read_bytes())
    expected = "window.IR_LESSON = " + json.dumps({"raw": raw, "run": report, "verdicts": verdicts}, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + ";\n"
    assert (folder / "data.js").read_text() == expected
    assert json.loads((root / "sources.json").read_text())["third_party_body_saved"] is False
    return raw


def negatives(raw):
    mutations = {
        "and-or-spoof": lambda x: x["queries"][0].__setitem__("doc_ids", ["d1","d2","d3","d4"]),
        "empty-query-match-all": lambda x: x["queries"][4].__setitem__("doc_ids", sorted(BASE)),
        "unknown-invented-hit": lambda x: x["queries"][5].__setitem__("doc_ids", ["d1"]),
        "stale-hidden": lambda x: x["queries"][9].__setitem__("doc_ids", []),
        "missing-hidden": lambda x: x["queries"][10].__setitem__("doc_ids", ["d1", "d3"]),
        "postings-shrink": lambda x: x["snapshots"][0]["index"]["postings"]["blue"].pop(),
        "tokenization-spoof": lambda x: x["queries"][2].__setitem__("terms", ["BLUE", "Green"]),
        "missing-query": lambda x: x["queries"].pop(),
        "intersection-spoof": lambda x: x["queries"][0]["posting_steps"][1].__setitem__("after", ["d1","d3"]),
        "semantic-overclaim": lambda x: x["scope"].__setitem__("semantic_embedding", True),
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
    raw = validate_saved()
    print("PASS: 13 executed queries, independent fullscan/postings/steps/hashes; 2 expected anomalies and rebuild recovery; negative=%d; read-only" % negatives(raw))
