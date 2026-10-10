#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Execute index construction, queries, stale-state anomalies and recovery in Python."""
import copy
import json
import platform
from indexer import build, content_hash, search, tokens

BASE = {"d1": "Blue green note", "d2": "Blue red memo", "d3": "Green gold note",
        "d4": "Red blue blue log", "d5": ""}
INITIAL_QUERIES = (
    ("and", "blue green", "AND"), ("or", "blue green", "OR"),
    ("case-punctuation", "BLUE, Green!", "AND"), ("duplicate", "blue blue", "AND"),
    ("empty", "  ...  ", "OR"), ("unknown", "violet", "AND"),
    ("unknown-and", "blue violet", "AND"), ("unknown-or", "blue violet", "OR"),
    ("ascii-boundary", "blue-green 東京", "AND"),
)


def run():
    original = copy.deepcopy(BASE)
    index = build(original)
    snapshots, queries = [], []

    def snapshot(name, documents, selected_index, built_documents):
        snapshots.append({"id": name, "documents": copy.deepcopy(documents),
                          "corpus_hash": content_hash(documents),
                          "indexed_documents": copy.deepcopy(built_documents),
                          "index": copy.deepcopy(selected_index),
                          "document_tokens": {key: tokens(text) for key, text in sorted(documents.items())}})

    def query(stage, case_id, text, mode, documents, selected_index):
        queries.append({"id": stage + "." + case_id, "stage": stage,
                        **search(selected_index, documents, text, mode)})

    snapshot("initial", original, index, original)
    for case_id, text, mode in INITIAL_QUERIES:
        query("initial", case_id, text, mode, original, index)
    current = copy.deepcopy(original)
    current["d1"] = "Gold green note"
    snapshot("stale", current, index, original)
    query("stale", "removed-blue", "blue green", "AND", current, index)
    query("stale", "added-gold", "gold green", "AND", current, index)
    rebuilt = build(current)
    snapshot("rebuilt", current, rebuilt, current)
    query("rebuilt", "removed-blue", "blue green", "AND", current, rebuilt)
    query("rebuilt", "added-gold", "gold green", "AND", current, rebuilt)
    return {"subject": "information-retrieval-search", "schema_version": 1,
            "runtime": {"python_version": platform.python_version(), "implementation": platform.python_implementation(),
                        "os": platform.system(), "architecture": platform.machine()},
            "input": {"initial_documents": BASE, "update": {"doc_id": "d1", "text": "Gold green note"},
                      "tokenizer": "lowercase then ASCII [a-z0-9]+ runs; duplicate terms collapsed per query",
                      "operators": ["AND", "OR"], "schedule": "build -> query -> update without rebuild -> query -> rebuild -> query"},
            "snapshots": snapshots, "queries": queries,
            "scope": {"actual": "executed Python stdlib inverted index with synthetic documents",
                      "ranked_retrieval": False, "bm25": False, "semantic_embedding": False,
                      "product_engine": False, "performance_benchmark": False,
                      "unicode_morphology": False}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, sort_keys=True, indent=2))
