"""Two real implementations of the application-owned port."""
import sqlite3
from dataclasses import astuple
from ports import Order, StoreConflict, StoreUnavailable


class MemoryAdapter:
    def __init__(self, emit):
        self.rows = {}
        self.unavailable = False
        self.emit = emit

    def add(self, order: Order):
        self.emit("port-add", adapter="memory", row=list(astuple(order)))
        if self.unavailable:
            try:
                raise OSError("injected-memory-store-unavailable")
            except OSError as exc:
                raise StoreUnavailable("memory-unavailable") from exc
        if order.id in self.rows:
            raise StoreConflict("memory-duplicate")
        self.rows[order.id] = order

    def snapshot(self):
        return [list(astuple(self.rows[key])) for key in sorted(self.rows)]

    def close(self):
        self.emit("adapter-closed", adapter="memory")


class SQLiteAdapter:
    def __init__(self, path, emit):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE orders(id TEXT PRIMARY KEY, sku TEXT NOT NULL, quantity INTEGER NOT NULL, total INTEGER NOT NULL)")
        self.db.commit()
        self.emit = emit
        self.db.set_trace_callback(lambda sql: emit("sql", sql=sql))

    def add(self, order: Order):
        self.emit("port-add", adapter="sqlite", row=list(astuple(order)))
        try:
            with self.db:
                self.db.execute("INSERT INTO orders VALUES (?, ?, ?, ?)", astuple(order))
        except sqlite3.IntegrityError as exc:
            raise StoreConflict("sqlite-duplicate") from exc
        except sqlite3.DatabaseError as exc:
            raise StoreUnavailable("sqlite-unavailable") from exc

    def close(self):
        self.db.close()
        self.emit("adapter-closed", adapter="sqlite")
