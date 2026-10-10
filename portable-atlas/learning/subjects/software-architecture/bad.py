"""Deliberately broken: core inspects adapters and bypasses their port contract."""
import sqlite3
from adapters import SQLiteAdapter
from domain import InvalidInput
from ports import Order


class TiedPlaceOrder:
    def __init__(self, orders):
        self.orders = orders

    def execute(self, payload):
        if (not isinstance(payload, dict)
                or not isinstance(payload.get("id"), str) or not payload["id"].strip()
                or not isinstance(payload.get("sku"), str) or not payload["sku"].strip()
                or not isinstance(payload.get("quantity"), int)
                or not 1 <= payload["quantity"] <= 100):
            raise InvalidInput("invalid-order")
        if isinstance(self.orders, SQLiteAdapter):
            # Adapter-specific rules have leaked into the domain.
            order = Order(payload["id"], payload["sku"], int(payload["quantity"]), payload["quantity"] * 100)
            try:
                with self.orders.db:
                    self.orders.db.execute("INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?)",
                                           (order.id, order.sku, order.quantity, order.total))
            except sqlite3.DatabaseError as exc:
                # Technical failure leaks as generic RuntimeError, not the port vocabulary.
                raise RuntimeError("leaked-sqlite-error") from exc
            return order
        order = Order(payload["id"].strip(), payload["sku"].strip(), int(payload["quantity"]), payload["quantity"] * 120)
        self.orders.add(order)
        return order
