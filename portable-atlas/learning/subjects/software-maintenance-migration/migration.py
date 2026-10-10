"""Finite staged SQLite migration. Exact mapping or explicitly lossy bad policy."""
import json
import re
import sqlite3
import sys
from decimal import Decimal
from pathlib import Path

V1 = 'CREATE TABLE "{}" (id TEXT PRIMARY KEY, amount_text TEXT NOT NULL, state TEXT NOT NULL)'
V2 = 'CREATE TABLE "{}" (id TEXT PRIMARY KEY, amount_cents INTEGER NOT NULL CHECK(amount_cents >= 0), state_code INTEGER NOT NULL)'
MAX_CENTS = 9223372036854775807


class Refusal(Exception):
    pass


def emit(event, **fields):
    print(json.dumps({"event": event, **fields}, ensure_ascii=False), flush=True)


def source_rows(db, version):
    columns = "id,amount_text,state" if version == 1 else "id,amount_cents,state_code"
    return db.execute(f"SELECT {columns} FROM orders ORDER BY id").fetchall()


def map_rows(rows, direction, policy):
    result = []
    for ident, amount, state in rows:
        if direction == "up":
            if state not in ("new", "paid"):
                raise Refusal("unknown-state:" + state)
            if policy == "exact":
                if not re.fullmatch(r"(?:0|[1-9][0-9]*)\.[0-9]{2}", amount):
                    raise Refusal("noncanonical-or-lossy-amount:" + amount)
                cents = int(Decimal(amount) * 100)
            else:
                # Deliberately bad: truncate exact decimal fractions of a cent.
                cents = int(Decimal(amount) * 100)
                emit("lossy-conversion", id=ident, original=amount, cents=cents)
            if not 0 <= cents <= MAX_CENTS:
                raise Refusal("amount-out-of-int64-range")
            result.append((ident, cents, {"new": 10, "paid": 20}[state]))
        else:
            if type(amount) is not int or not 0 <= amount <= MAX_CENTS:
                raise Refusal("invalid-cents")
            if state not in (10, 20):
                raise Refusal("unknown-state-code:" + str(state))
            result.append((ident, f"{amount // 100}.{amount % 100:02d}", {10: "new", 20: "paid"}[state]))
    return result


def migrate(path, command):
    if (command.get("direction") not in ("up", "down")
            or command.get("policy") not in ("exact", "lossy")
            or command.get("inject") not in ("none", "after-copy", "after-drop")
            or command["direction"] == "down" and command["policy"] != "exact"):
        emit("refused", reason="unsupported-command")
        return 2
    db = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None)
    db.set_trace_callback(lambda sql: emit("sql", sql=sql))
    before_version = 1 if command["direction"] == "up" else 2
    after_version = 3 - before_version
    try:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version != before_version:
            raise Refusal("unsupported-source-version:" + str(version))
        schema = db.execute("SELECT sql FROM sqlite_schema WHERE type='table' AND name='orders'").fetchone()
        expected_schema = (V1 if before_version == 1 else V2).format("orders")
        if schema != (expected_schema,):
            raise Refusal("unsupported-source-schema")
        extra = db.execute("SELECT name FROM sqlite_schema WHERE name NOT IN ('orders','sqlite_autoindex_orders_1')").fetchall()
        if extra:
            raise Refusal("dependent-or-extra-schema-not-supported")
        rows = source_rows(db, before_version)
        mapped = map_rows(rows, command["direction"], command["policy"])
        emit("preflight-accepted", direction=command["direction"], policy=command["policy"], rows=len(rows))
        db.execute("BEGIN IMMEDIATE")
        if source_rows(db, before_version) != rows:
            raise Refusal("source-changed-after-preflight")
        db.execute((V1 if after_version == 1 else V2).format("orders_staged"))
        db.executemany("INSERT INTO orders_staged VALUES (?, ?, ?)", mapped)
        emit("staged-copy", mapped_rows=mapped)
        if command["inject"] == "after-copy":
            raise RuntimeError("injected-after-copy")
        db.execute("DROP TABLE orders")
        emit("old-table-dropped")
        if command["inject"] == "after-drop":
            raise RuntimeError("injected-after-drop")
        db.execute('ALTER TABLE orders_staged RENAME TO "orders"')
        db.execute(f"PRAGMA user_version={after_version}")
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("integrity-failed")
        db.execute("COMMIT")
        emit("migrated", version=after_version)
        return 0
    except Refusal as exc:
        if db.in_transaction:
            db.execute("ROLLBACK")
        emit("refused", reason=str(exc))
        return 2
    except (RuntimeError, sqlite3.DatabaseError) as exc:
        if db.in_transaction:
            db.execute("ROLLBACK")
        emit("rolled-back", reason=str(exc))
        return 3
    finally:
        emit("transaction-after-step", active=db.in_transaction)
        db.close()
        try:
            db.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            emit("connection-closed", probe="ProgrammingError")
        else:
            raise AssertionError("connection leaked")


if __name__ == "__main__":
    raise SystemExit(migrate(sys.argv[1], json.load(sys.stdin)))
