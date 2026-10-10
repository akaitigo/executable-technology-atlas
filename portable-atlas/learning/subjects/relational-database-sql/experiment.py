#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Execute the bounded SQL lesson against an in-memory SQLite database."""

import json
import sqlite3
import sys


QUERY_SPECS = (
    (
        "null.equals-null",
        "SELECT id, label FROM rows WHERE score = NULL ORDER BY id",
    ),
    (
        "null.is-null",
        "SELECT id, label FROM rows WHERE score IS NULL ORDER BY id",
    ),
    (
        "null.truth-values",
        "SELECT NULL = NULL AS null_eq_null, NULL IS NULL AS null_is_null, "
        "(NULL = NULL) OR 1 AS unknown_or_true, "
        "(NULL = NULL) AND 0 AS unknown_and_false",
    ),
    (
        "join.inner",
        "SELECT r.id AS row_id, r.label, e.id AS event_id, e.kind "
        "FROM rows AS r INNER JOIN events AS e ON e.row_id = r.id "
        "ORDER BY r.id, e.id",
    ),
    (
        "join.left",
        "SELECT r.id AS row_id, r.label, e.id AS event_id, e.kind "
        "FROM rows AS r LEFT JOIN events AS e ON e.row_id = r.id "
        "ORDER BY r.id, e.id",
    ),
    (
        "join.left-where",
        "SELECT r.id AS row_id, r.label, e.id AS event_id, e.kind "
        "FROM rows AS r LEFT JOIN events AS e ON e.row_id = r.id "
        "WHERE e.kind = 'keep' ORDER BY r.id, e.id",
    ),
    (
        "join.left-on",
        "SELECT r.id AS row_id, r.label, e.id AS event_id, e.kind "
        "FROM rows AS r LEFT JOIN events AS e "
        "ON e.row_id = r.id AND e.kind = 'keep' ORDER BY r.id, e.id",
    ),
)


def query(conn, query_id, sql):
    cursor = conn.execute(sql)
    columns = [description[0] for description in cursor.description]
    return {
        "id": query_id,
        "sql": sql,
        "columns": columns,
        "rows": [dict(row) for row in cursor.fetchall()],
    }


def rejected(conn, case_id, sql, parameters):
    try:
        conn.execute(sql, parameters)
    except sqlite3.IntegrityError as error:
        conn.rollback()
        return {
            "id": case_id,
            "sql": sql,
            "parameters": list(parameters),
            "accepted": False,
            "error_type": type(error).__name__,
            "sqlite_errorcode": getattr(error, "sqlite_errorcode", None),
            "sqlite_errorname": getattr(error, "sqlite_errorname", None),
            "message": str(error),
        }
    conn.rollback()
    return {
        "id": case_id,
        "sql": sql,
        "parameters": list(parameters),
        "accepted": True,
        "error_type": None,
        "sqlite_errorcode": None,
        "sqlite_errorname": None,
        "message": None,
    }


def run():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE rows (
          id INTEGER PRIMARY KEY,
          label TEXT NOT NULL,
          score INTEGER,
          code TEXT UNIQUE
        );
        CREATE TABLE events (
          id INTEGER PRIMARY KEY,
          row_id INTEGER NOT NULL REFERENCES rows(id),
          kind TEXT NOT NULL,
          note TEXT NOT NULL
        );
        INSERT INTO rows(id, label, score, code) VALUES
          (1, 'alpha', 10, 'A'),
          (2, 'beta', NULL, NULL),
          (3, 'gamma', 20, NULL);
        INSERT INTO events(id, row_id, kind, note) VALUES
          (101, 1, 'keep', 'first'),
          (102, 1, 'review', 'second'),
          (103, 2, 'review', 'third');
        """
    )
    conn.commit()

    queries = [query(conn, query_id, sql) for query_id, sql in QUERY_SPECS]
    constraint_cases = [
        rejected(
            conn,
            "constraint.not-null",
            "INSERT INTO events(id, row_id, kind, note) VALUES (?, ?, ?, ?)",
            (201, 1, "keep", None),
        ),
        rejected(
            conn,
            "constraint.unique-non-null",
            "INSERT INTO rows(id, label, score, code) VALUES (?, ?, ?, ?)",
            (4, "delta", 30, "A"),
        ),
        rejected(
            conn,
            "constraint.foreign-key",
            "INSERT INTO events(id, row_id, kind, note) VALUES (?, ?, ?, ?)",
            (202, 99, "keep", "orphan"),
        ),
    ]
    unique_null_count = conn.execute(
        "SELECT count(*) FROM rows WHERE code IS NULL"
    ).fetchone()[0]
    foreign_keys = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    source_id = conn.execute("SELECT sqlite_source_id()").fetchone()[0]
    payload = {
        "schema_version": 1,
        "subject": "relational-database-sql",
        "execution": {
            "engine": "SQLite",
            "database": ":memory:",
            "sqlite_version": sqlite3.sqlite_version,
            "sqlite_source_id": source_id,
            "python_version": ".".join(map(str, sys.version_info[:3])),
            "foreign_keys_pragma": foreign_keys,
            "attempts": 1,
            "retries": 0,
        },
        "fixture": {
            "rows": [
                {"id": 1, "label": "alpha", "score": 10, "code": "A"},
                {"id": 2, "label": "beta", "score": None, "code": None},
                {"id": 3, "label": "gamma", "score": 20, "code": None},
            ],
            "events": [
                {"id": 101, "row_id": 1, "kind": "keep", "note": "first"},
                {"id": 102, "row_id": 1, "kind": "review", "note": "second"},
                {"id": 103, "row_id": 2, "kind": "review", "note": "third"},
            ],
        },
        "queries": queries,
        "constraints": {
            "foreign_keys_pragma": foreign_keys,
            "unique_null_rows": unique_null_count,
            "cases": constraint_cases,
        },
        "classification": {
            "actual": "Python stdlib sqlite3 against one in-memory SQLite database",
            "explanatory": "The browser sequence and labels interpret the saved rows; they are not a second database execution.",
            "not_observed": [
                "PostgreSQL execution",
                "other SQL dialects",
                "query planner behavior",
                "concurrent transactions",
            ],
        },
    }
    conn.close()
    return payload


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))
