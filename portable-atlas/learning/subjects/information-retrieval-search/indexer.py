#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""An intentionally small ASCII Boolean inverted index, without ranking."""
import hashlib
import json
import re


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def content_hash(value):
    content = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(content).hexdigest()


def build(documents):
    postings = {}
    for doc_id, text in sorted(documents.items()):
        for term in set(tokens(text)):
            postings.setdefault(term, []).append(doc_id)
    return {"built_from_corpus_hash": content_hash(documents),
            "postings": dict(sorted(postings.items())), "postings_hash": content_hash(postings)}


def search(index, documents, query, operator):
    if operator not in ("AND", "OR"):
        raise ValueError("Only explicit AND/OR mode is supported")
    terms = list(dict.fromkeys(tokens(query)))
    result, steps = None, []
    for term in terms:
        posting = set(index["postings"].get(term, []))
        before = None if result is None else sorted(result)
        result = posting if result is None else (result & posting if operator == "AND" else result | posting)
        steps.append({"term": term, "posting": sorted(posting), "before": before, "after": sorted(result)})
    ids = [] if result is None else sorted(result)
    return {"query": query, "operator": operator, "terms": terms,
            "status": "empty-query" if not terms else "ok", "posting_steps": steps,
            "doc_ids": ids, "rows": [{"id": doc_id, "text": documents[doc_id]} for doc_id in ids]}
