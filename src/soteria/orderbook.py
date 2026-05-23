"""In-memory Decimal order book for Coinbase level2 events."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from time import monotonic

from soteria.models import BookUpdate, Level2Event, PriceLevel


class OrderBook:
    """Maintain bids and asks for one product from absolute-quantity updates."""

    def __init__(self, product_id: str) -> None:
        self.product_id = product_id
        self.bids: dict[Decimal, Decimal] = {}
        self.asks: dict[Decimal, Decimal] = {}
        self.message_count = 0
        self.last_event_time: datetime | None = None
        self.connection_status = "disconnected"
        self._message_times: deque[float] = deque()

    def apply_event(self, event: Level2Event, received_at: float | None = None) -> None:
        """Apply one parsed event and update stream accounting."""

        if event.product_id != self.product_id:
            return
        if event.kind == "snapshot":
            self.apply_snapshot(event.updates)
        else:
            self.apply_updates(event.updates)

        self.message_count += 1
        self.connection_status = "connected"
        self._message_times.append(monotonic() if received_at is None else received_at)
        event_times = [
            update.event_time for update in event.updates if update.event_time is not None
        ]
        self.last_event_time = max(event_times) if event_times else datetime.now(UTC)

    def apply_snapshot(self, updates: Iterable[BookUpdate]) -> None:
        """Replace all known levels with those supplied in a snapshot."""

        self.bids.clear()
        self.asks.clear()
        self.apply_updates(updates)

    def apply_updates(self, updates: Iterable[BookUpdate]) -> None:
        """Apply absolute quantity updates, removing levels whose size becomes zero."""

        for update in updates:
            side = self.bids if update.side == "bid" else self.asks
            if update.quantity == 0:
                side.pop(update.price, None)
            else:
                side[update.price] = update.quantity

    def top_bids(self, levels: int) -> tuple[PriceLevel, ...]:
        """Return highest bid prices first."""

        prices = sorted(self.bids, reverse=True)[:levels]
        return tuple(PriceLevel(price, self.bids[price]) for price in prices)

    def top_asks(self, levels: int) -> tuple[PriceLevel, ...]:
        """Return lowest ask prices first."""

        prices = sorted(self.asks)[:levels]
        return tuple(PriceLevel(price, self.asks[price]) for price in prices)

    def best_bid(self) -> PriceLevel | None:
        """Return the highest bid or ``None`` for an empty side."""

        bids = self.top_bids(1)
        return bids[0] if bids else None

    def best_ask(self) -> PriceLevel | None:
        """Return the lowest ask or ``None`` for an empty side."""

        asks = self.top_asks(1)
        return asks[0] if asks else None

    def messages_per_second(self, now: float | None = None, window_seconds: float = 1.0) -> float:
        """Measure received level2 event rate over a short trailing window."""

        current_time = monotonic() if now is None else now
        cutoff = current_time - window_seconds
        while self._message_times and self._message_times[0] < cutoff:
            self._message_times.popleft()
        return len(self._message_times) / window_seconds
