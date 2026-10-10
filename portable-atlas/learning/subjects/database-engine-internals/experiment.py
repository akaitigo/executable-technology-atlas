#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Observe three query plans in an actual, isolated in-memory SQLite connection."""
import json
import platform
import sqlite3

SCHEMA = "CREATE TABLE samples (id INTEGER PRIMARY KEY, bucket INTEGER NOT NULL, label TEXT NOT NULL)"
INDEX = "CREATE INDEX samples_bucket_idx ON samples(bucket)"
INSERT = "INSERT INTO samples(id, bucket, label) VALUES (?, ?, ?)"
EQUALITY = "SELECT id, bucket, label FROM samples WHERE bucket = ? ORDER BY id"
EXPRESSION = "SELECT id, bucket, label FROM samples WHERE bucket + 0 = ? ORDER BY id"


def capture(conn, case_id, query):
    plan_cursor = conn.execute("EXPLAIN QUERY PLAN " + query, (7,))
    plan = {"columns": [x[0] for x in plan_cursor.description],
            "rows": [list(x) for x in plan_cursor.fetchall()]}
    result_cursor = conn.execute(query, (7,))
    return {
        "id": case_id, "query": query, "parameters": [7],
        "explain_query": "EXPLAIN QUERY PLAN " + query,
        "plan": plan,
        "columns": [x[0] for x in result_cursor.description],
        "rows": [list(x) for x in result_cursor.fetchall()],
        "schema_objects": [list(x) for x in conn.execute(
            "SELECT type, name, sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name")],
    }


def run():
    fixture = [[i, i % 16, "row-%03d" % i] for i in range(1, 257)]
    with sqlite3.connect(":memory:") as conn:
        conn.execute(SCHEMA)
        conn.executemany(INSERT, fixture)
        conn.commit()
        baseline = capture(conn, "no-index-equality", EQUALITY)
        conn.execute(INDEX)
        conn.commit()
        equality = capture(conn, "indexed-equality", EQUALITY)
        expression = capture(conn, "indexed-expression", EXPRESSION)
        actual_fixture = [list(x) for x in conn.execute("SELECT id, bucket, label FROM samples ORDER BY id")]
        result = {
            "schema_version": 1, "subject": "database-engine-internals",
            "runtime": {"engine": "SQLite", "sqlite_version": sqlite3.sqlite_version,
                        "sqlite_source_id": conn.execute("SELECT sqlite_source_id()").fetchone()[0],
                        "python_version": platform.python_version(), "implementation": platform.python_implementation(),
                        "database": ":memory:"},
            "setup": {"schema_sql": SCHEMA, "index_sql": INDEX, "insert_sql": INSERT,
                      "fixture_rows": actual_fixture, "fixture_count": len(actual_fixture),
                      "distribution": "id=1..256; bucket=id%16; label=row-%03d"},
            "cases": [baseline, equality, expression],
            "scope": {"classification": "actual-sqlite-query-plan-and-results",
                      "time_benchmark_performed": False, "speedup_claimed": False,
                      "physical_page_trace": False, "wal_crash_recovery": False,
                      "other_database_executed": False},
        }
    conn.close()
    return result


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, sort_keys=True, indent=2))
