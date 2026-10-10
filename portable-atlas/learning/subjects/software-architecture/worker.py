"""Composition root + CLI incoming adapter. One process per variant/scenario."""
import json
import sqlite3
import sys
from dataclasses import astuple
from pathlib import Path
sys.dont_write_bytecode = True
from adapters import MemoryAdapter, SQLiteAdapter
from bad import TiedPlaceOrder
from domain import PlaceOrder, InvalidInput, DuplicateOrder, DependencyUnavailable


def emit(event, **fields):
    print(json.dumps({"event": event, **fields}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    variant, storage, directory = sys.argv[1:]
    case = Path(directory)
    inputs = json.load(sys.stdin)
    repo = MemoryAdapter(emit) if storage == "memory" else SQLiteAdapter(case / "orders.sqlite", emit)
    usecase = PlaceOrder(repo) if variant == "port" else TiedPlaceOrder(repo)
    emit("composition", variant=variant, storage=storage, usecase=type(usecase).__name__)
    responses = []
    try:
        for i, command in enumerate(inputs):
            emit("request-start", index=i, payload=command["payload"])
            if command.get("unavailable"):
                if storage == "memory":
                    repo.unavailable = True
                else:
                    repo.db.close()  # Real sqlite ProgrammingError on a closed handle.
                emit("injected-storage-unavailable", storage=storage)
            try:
                order = usecase.execute(command["payload"])
                response = {"status": 201, "body": list(astuple(order))}
            except InvalidInput:
                response = {"status": 422, "error": "invalid-order"}
            except DuplicateOrder:
                response = {"status": 409, "error": "duplicate-order"}
            except DependencyUnavailable as exc:
                emit("translated-exception", chain=[type(exc).__name__, type(exc.__cause__).__name__, type(exc.__cause__.__cause__).__name__])
                response = {"status": 503, "error": "storage-unavailable"}
            except Exception as exc:
                emit("untranslated-exception", type=type(exc).__name__)
                response = {"status": 500, "error": "untranslated-storage-error"}
            responses.append(response)
            emit("response", index=i, **response)
    finally:
        repo.close()
    if storage == "memory":
        rows = repo.snapshot()
        (case / "memory-final.json").write_text(json.dumps(rows, ensure_ascii=False) + "\n")
    else:
        # Actual on-disk state read through a new connection, not domain results.
        db = sqlite3.connect((case / "orders.sqlite").resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
        try:
            rows = [list(x) for x in db.execute("SELECT id,sku,quantity,total FROM orders ORDER BY id")]
        finally:
            db.close()
    emit("final-state", rows=rows)
