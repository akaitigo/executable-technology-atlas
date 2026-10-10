#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Execute a single order-grain metric and deliberate SQL fan-out in SQLite."""
import hashlib
import json
import platform
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
INPUT = {"customers": [[10, "north"], [20, "south"]],
         "orders": [[1, 10, 100], [2, 10, 100], [3, 999, 80], [4, None, None], [5, 20, 50], [6, 20, 0]],
         "lines": [[101, 1], [102, 1], [201, 2], [301, 3], [401, 4], [601, 6]]}
METRIC = {"id": "eligible-order-known-amount", "grain": "one row per order_id",
          "eligibility": "at least one line exists", "amount_unit": "synthetic integer units",
          "null_policy": "SUM known amount; preserve NULL when none known; report missing count",
          "dimension_policy": "retain NULL_KEY and UNKNOWN_KEY separately; no actual customer data"}
SCHEMA = """CREATE TABLE customers(customer_id INTEGER PRIMARY KEY, region TEXT NOT NULL);
CREATE TABLE orders(order_id INTEGER PRIMARY KEY, customer_id INTEGER, amount INTEGER);
CREATE TABLE lines(line_id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(order_id));"""


def run():
    db = sqlite3.connect(":memory:")
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(SCHEMA)
        db.executemany("INSERT INTO customers VALUES (?,?)", INPUT["customers"])
        db.executemany("INSERT INTO orders VALUES (?,?,?)", INPUT["orders"])
        db.executemany("INSERT INTO lines VALUES (?,?)", INPUT["lines"])
        specification = json.loads((HERE / "queries.json").read_text())
        queries = []
        for spec in specification:
            entry = dict(spec)
            for kind in ("relation", "metric"):
                cursor = db.execute(spec[kind + "_sql"])
                entry[kind + "_columns"] = [column[0] for column in cursor.description]
                entry[kind + "_rows"] = [list(row) for row in cursor.fetchall()]
            queries.append(entry)
        return {"subject": "analytics-data-platform", "schema_version": 1,
                "runtime": {"python_version": platform.python_version(), "sqlite_version": sqlite3.sqlite_version,
                            "sqlite_source_id": db.execute("SELECT sqlite_source_id()").fetchone()[0],
                            "os": platform.system(), "architecture": platform.machine(), "database": "in-memory",
                            "foreign_keys": db.execute("PRAGMA foreign_keys").fetchone()[0]},
                "input": INPUT, "input_digest": "sha256:" + hashlib.sha256(json.dumps(INPUT, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                "schema_sql": SCHEMA, "metric_definition": METRIC, "queries": queries,
                "scope": {"actual": "SQLite order/line grain SQL on synthetic data", "warehouse_product": False,
                          "lake_product": False, "bi_product": False, "performance_benchmark": False,
                          "distributed_pipeline": False, "financial_accounting": False}}
    finally:
        db.close()


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, sort_keys=True, indent=2))
