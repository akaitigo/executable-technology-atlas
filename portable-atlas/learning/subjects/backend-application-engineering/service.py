"""Finite request handler: real SQLite, explicit request-owned connections."""
import json
import sqlite3
import sys


def emit(event, **fields):
    print(json.dumps({"event": event, **fields}, ensure_ascii=False), flush=True)


def handle(path, request):
    # Validation belongs before acquiring a database resource or BEGIN.
    if (not isinstance(request, dict) or not isinstance(request.get("id"), str)
            or not request["id"].strip() or not isinstance(request.get("name"), str)
            or not request["name"].strip() or type(request.get("quantity")) is not int
            or not 1 <= request["quantity"] <= 100
            or request.get("mode") not in ("atomic", "nonatomic")
            or type(request.get("fail_second", False)) is not bool):
        emit("validation-rejected", status=422)
        return
    emit("validation-accepted", id=request["id"])
    db = sqlite3.connect(path, isolation_level=None)
    emit("connection-opened", id=request["id"])
    db.set_trace_callback(lambda sql: emit("sql", sql=sql))
    try:
        db.execute("PRAGMA foreign_keys=ON")
        if request["mode"] == "atomic":
            db.execute("BEGIN IMMEDIATE")
        db.execute("INSERT INTO orders VALUES (?, ?, ?)",
                   (request["id"], request["name"], request["quantity"]))
        emit("order-created", in_transaction=db.in_transaction)
        # Inject an actual second SQL statement NOT NULL failure.
        payload = None if request.get("fail_second") else json.dumps({"quantity": request["quantity"]})
        db.execute("INSERT INTO outbox VALUES (?, 'OrderCreated', ?)", (request["id"], payload))
        if db.in_transaction:
            db.execute("COMMIT")
        emit("response", status=201, id=request["id"])
    except sqlite3.IntegrityError as exc:
        emit("database-error", error=str(exc), in_transaction=db.in_transaction)
        if db.in_transaction:
            db.execute("ROLLBACK")
        emit("response", status=409 if "UNIQUE" in str(exc) else 500, id=request["id"])
    finally:
        emit("transaction-after-request", active=db.in_transaction)
        db.close()
        # Actual closed-handle probe, not a variable named "closed".
        try:
            db.execute("SELECT 1")
        except sqlite3.ProgrammingError:
            emit("connection-closed", probe="ProgrammingError")
        else:
            raise AssertionError("connection leaked")


if __name__ == "__main__":
    for request in json.load(sys.stdin):
        handle(sys.argv[1], request)
