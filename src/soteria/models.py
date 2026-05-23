"""Small, typed data structures shared by Soteria modules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

BookSide = Literal["bid", "ask"]
EventKind = Literal["snapshot", "update"]


@dataclass(frozen=True, slots=True)
class PriceLevel:
    """A quantity available at a single order-book price."""

    price: Decimal
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class BookUpdate:
    """An absolute replacement quantity for one side and price level."""

    side: BookSide
    price: Decimal
    quantity: Decimal
    event_time: datetime | None = None


@dataclass(frozen=True, slots=True)
class Level2Event:
    """A Coinbase level2 snapshot or incremental update."""

    kind: EventKind
    product_id: str
    updates: tuple[BookUpdate, ...]


@dataclass(frozen=True, slots=True)
class MarketMetrics:
    """A display-ready set of order-book statistics."""

    best_bid: Decimal | None
    best_ask: Decimal | None
    spread: Decimal | None
    mid_price: Decimal | None
    top_n_bid_depth: Decimal
    top_n_ask_depth: Decimal
    top_n_imbalance: Decimal
    message_count: int
    messages_per_second: float
    last_event_time: datetime | None
    connection_status: str


@dataclass(frozen=True, slots=True)
class FeatureVector:
    """One numerical feature row suitable for persistence or inference."""

    timestamp: datetime
    product_id: str
    values: dict[str, float]

    def as_row(self) -> dict[str, str | float]:
        """Return values in CSV-friendly form."""

        return {
            "timestamp": self.timestamp.isoformat(),
            "product_id": self.product_id,
            **self.values,
        }
