#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Two actual SQLite connections, manually interleaved committed statements."""
import json
import platform
import sqlite3
from kv import READ, BLIND, compare_and_swap

SCHEMA = "CREATE TABLE kv (key TEXT PRIMARY KEY NOT NULL, value INTEGER NOT NULL CHECK(typeof(value) = 'integer'), version INTEGER NOT NULL CHECK(typeof(version) = 'integer' AND version >= 0))"
STATE_SQL = "SELECT key, value, version FROM kv ORDER BY key"
SEED = "INSERT INTO kv(key, value, version) VALUES (?, ?, ?)"


class Session:
    def __init__(self, connection, name, trace):
        self.connection, self.name, self.trace = connection, name, trace

    def state(self):
        return [list(row) for row in self.connection.execute(STATE_SQL)]

    def execute(self, operation, sql, params):
        cursor = self.connection.execute(sql, params)
        rows = [list(row) for row in cursor.fetchall()] if cursor.description else []
        entry = {"step": len(self.trace)+1, "session": self.name, "operation": operation,
                 "sql": sql, "parameters": params, "rowcount": cursor.rowcount, "rows": rows,
                 "state_sql": STATE_SQL, "state_after": self.state(),
                 "autocommit_transaction_open_after": self.connection.in_transaction}
        self.trace.append(entry)
        return entry

    def reject(self, key, value, expected_version, reason):
        entry = {"step": len(self.trace)+1, "session": self.name, "operation": "invalid-input",
                 "sql": None, "parameters": [value, key, expected_version], "rowcount": None,
                 "rows": [], "reason": reason, "state_sql": STATE_SQL, "state_after": self.state(),
                 "autocommit_transaction_open_after": self.connection.in_transaction}
        self.trace.append(entry)
        return entry


def scenario(name):
    # Named memory database shared only by these two sequentially used connections.
    uri = "file:atlas_kv_" + name + "?mode=memory&cache=shared"
    a_conn = sqlite3.connect(uri, uri=True, isolation_level=None)
    b_conn = sqlite3.connect(uri, uri=True, isolation_level=None)
    try:
        a_conn.execute(SCHEMA)
        a_conn.execute(SEED, ("counter", 0, 1))
        trace = []
        a, b = Session(a_conn, "A", trace), Session(b_conn, "B", trace)
        if name in ("blind", "cas"):
            first = a.execute("read", READ, ["counter"])["rows"][0]
            second = b.execute("read", READ, ["counter"])["rows"][0]
            if name == "blind":
                a.execute("blind", BLIND, [first[0]+1, "counter"])
                b.execute("blind", BLIND, [second[0]+1, "counter"])
            else:
                compare_and_swap(a, "counter", first[0]+1, first[1])
                compare_and_swap(b, "counter", second[0]+1, second[1])
                latest = b.execute("read", READ, ["counter"])["rows"][0]
                compare_and_swap(b, "counter", latest[0]+1, latest[1])
        elif name == "invalid-types":
            for value, expected in [(1, "1"), (1, True), (1, -1), (1.5, 1), ("1", 1), (True, 1)]:
                compare_and_swap(a, "counter", value, expected)
        elif name == "unknown-key":
            a.execute("read", READ, ["missing"])
            compare_and_swap(a, "missing", 1, 1)
            compare_and_swap(a, "counter", 1, 0)
        elif name == "aba":
            old = a.execute("read", READ, ["counter"])["rows"][0]
            compare_and_swap(b, "counter", 5, 1)
            compare_and_swap(b, "counter", 0, 2)
            compare_and_swap(a, "counter", 1, old[1])
        elif name == "aba-reset":
            old = a.execute("read", READ, ["counter"])["rows"][0]
            b.execute("delete", "DELETE FROM kv WHERE key = ?", ["counter"])
            b.execute("recreate", SEED, ["counter", 0, 1])
            compare_and_swap(a, "counter", 1, old[1])
        return {"id": name, "connection_count": 2, "distinct_connection_objects": a_conn is not b_conn,
                "database_uri": uri, "initial": [["counter", 0, 1]], "trace": trace,
                "final": a.state(), "final_sql": STATE_SQL}
    finally:
        a_conn.close()
        b_conn.close()


def run():
    with sqlite3.connect(":memory:") as identity:
        source_id = identity.execute("SELECT sqlite_source_id()").fetchone()[0]
    identity.close()
    return {"subject": "operational-data-stores", "schema_version": 1,
            "runtime": {"engine": "SQLite", "sqlite_version": sqlite3.sqlite_version,
                        "sqlite_source_id": source_id, "python_version": platform.python_version(),
                        "implementation": platform.python_implementation(), "os": platform.system(),
                        "architecture": platform.machine()},
            "setup": {"schema_sql": SCHEMA, "seed_sql": SEED, "seed_parameters": ["counter", 0, 1],
                      "session_count_per_scenario": 2, "isolation_level": None,
                      "schedule": "fixed sequential autocommit statements; no parallel threads"},
            "scenarios": [scenario(name) for name in ("blind", "cas", "invalid-types", "unknown-key", "aba", "aba-reset")],
            "scope": {"actual": "two SQLite connections to named shared in-memory databases",
                      "locking_tested": False, "parallel_performance_measured": False,
                      "redis_executed": False, "cache_document_graph_implemented": False,
                      "aba_key_recreation_protected": False}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, sort_keys=True, indent=2))
