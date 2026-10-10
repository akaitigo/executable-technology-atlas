"""One real SQLite consumer process; transport/ack is the finite driver's model."""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def emit(kind, **fields):
    print(json.dumps({"event": kind, "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), **fields}, ensure_ascii=False), flush=True)


def init_db(path):
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA journal_mode=DELETE")
        db.execute("PRAGMA synchronous=FULL")
        db.executescript("""
            CREATE TABLE inbox(event_id TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE effects(sequence INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL, delta INTEGER NOT NULL);
            CREATE TABLE account(id TEXT PRIMARY KEY, balance INTEGER NOT NULL);
            INSERT INTO account VALUES('demo', 0);
        """)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    arg = parser.parse_args()
    if not re.fullmatch(r"observations/[0-9TZ]+-events/[a-z0-9-]+/consumer.sqlite", arg.db):
        raise SystemExit("invalid task-owned database path")
    path = ROOT / arg.db
    if ROOT not in path.resolve().parents or not path.is_file():
        raise SystemExit("database must exist inside module")
    request = json.load(sys.stdin)
    event, policy, fault = request["message"], request["policy"], request["fault"]
    emit("consumer-start", pid=os.getpid(), sqlite_version=sqlite3.sqlite_version, policy=policy, fault=fault)
    if policy not in ("inbox", "naive") or fault not in ("none", "crash-after-commit", "rollback-before-commit"):
        raise SystemExit("unsupported consumer request")
    payload = event["payload"]
    if type(payload) is not dict or set(payload) != {"account", "delta"} or payload["account"] != "demo" or type(payload["delta"]) is not int or not -10 <= payload["delta"] <= 10:
        emit("poison", reason="invalid-payload")
        return 65
    payload_bytes = canonical(payload)
    fingerprint = "sha256:" + hashlib.sha256(payload_bytes).hexdigest()
    db = sqlite3.connect(path, isolation_level=None)
    db.execute("PRAGMA synchronous=FULL")
    db.set_trace_callback(lambda sql: emit("sqlite-sql", sql=sql))
    db.execute("BEGIN IMMEDIATE")
    if policy == "inbox":
        existing = db.execute("SELECT fingerprint,payload FROM inbox WHERE event_id=?", (event["id"],)).fetchone()
        if existing:
            db.rollback()
            db.close()
            if existing != (fingerprint, payload_bytes.decode()):
                emit("identity-conflict", event_id=event["id"], incoming_fingerprint=fingerprint, stored_fingerprint=existing[0])
                return 66
            emit("duplicate-no-effect", event_id=event["id"], fingerprint=fingerprint)
            emit("ack-eligible", event_id=event["id"])
            return 0
        db.execute("INSERT INTO inbox VALUES(?,?,?)", (event["id"], fingerprint, payload_bytes.decode()))
    db.execute("INSERT INTO effects(event_id,delta) VALUES(?,?)", (event["id"], payload["delta"]))
    db.execute("UPDATE account SET balance=balance+? WHERE id='demo'", (payload["delta"],))
    if fault == "rollback-before-commit":
        db.rollback()
        db.close()
        emit("transaction-rolled-back", event_id=event["id"], reason="injected-transient")
        return 75
    db.commit()
    emit("transaction-committed", event_id=event["id"], fingerprint=fingerprint)
    if fault == "crash-after-commit":
        emit("injected-process-crash-before-ack", event_id=event["id"], exit_code=70)
        os._exit(70)
    db.close()
    emit("ack-eligible", event_id=event["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
