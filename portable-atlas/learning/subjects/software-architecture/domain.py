"""Same use case for both adapters. Only application-owned port is imported."""
from ports import Order, OrdersPort, StoreConflict, StoreUnavailable


class InvalidInput(Exception):
    pass


class DuplicateOrder(Exception):
    pass


class DependencyUnavailable(Exception):
    pass


class PlaceOrder:
    def __init__(self, orders: OrdersPort):
        self.orders = orders

    def execute(self, payload):
        if (not isinstance(payload, dict)
                or not isinstance(payload.get("id"), str) or not payload["id"].strip()
                or not isinstance(payload.get("sku"), str) or not payload["sku"].strip()
                or type(payload.get("quantity")) is not int
                or not 1 <= payload["quantity"] <= 100):
            raise InvalidInput("invalid-order")
        order = Order(payload["id"].strip(), payload["sku"].strip(), payload["quantity"], payload["quantity"] * 120)
        try:
            self.orders.add(order)
        except StoreConflict as exc:
            raise DuplicateOrder("duplicate-order") from exc
        except StoreUnavailable as exc:
            raise DependencyUnavailable("storage-unavailable") from exc
        return order
