"""Application-owned contract; no adapter knowledge."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Order:
    id: str
    sku: str
    quantity: int
    total: int


class StoreConflict(Exception):
    pass


class StoreUnavailable(Exception):
    pass


class OrdersPort(Protocol):
    # add must preserve all four values, never replace an existing ID.
    # Duplicate ID => StoreConflict; unavailable storage => StoreUnavailable.
    def add(self, order: Order) -> None: ...
