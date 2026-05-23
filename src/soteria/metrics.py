"""Market-depth calculations derived from the live order book."""

from __future__ import annotations

from decimal import Decimal

from soteria.models import MarketMetrics, PriceLevel
from soteria.orderbook import OrderBook

ZERO = Decimal("0")


def depth(levels: tuple[PriceLevel, ...]) -> Decimal:
    """Sum quantities at selected price levels."""

    return sum((level.quantity for level in levels), start=ZERO)


def imbalance(bid_depth: Decimal, ask_depth: Decimal) -> Decimal:
    """Return normalized depth imbalance in the interval [-1, 1]."""

    total_depth = bid_depth + ask_depth
    return (bid_depth - ask_depth) / total_depth if total_depth else ZERO


def calculate_metrics(book: OrderBook, levels: int = 10) -> MarketMetrics:
    """Compute display and feature metrics for the top of the book."""

    best_bid_level = book.best_bid()
    best_ask_level = book.best_ask()
    best_bid = best_bid_level.price if best_bid_level else None
    best_ask = best_ask_level.price if best_ask_level else None
    if best_bid is not None and best_ask is not None:
        spread = best_ask - best_bid
        mid_price = (best_ask + best_bid) / Decimal("2")
    else:
        spread = None
        mid_price = None

    bid_depth = depth(book.top_bids(levels))
    ask_depth = depth(book.top_asks(levels))
    return MarketMetrics(
        best_bid=best_bid,
        best_ask=best_ask,
        spread=spread,
        mid_price=mid_price,
        top_n_bid_depth=bid_depth,
        top_n_ask_depth=ask_depth,
        top_n_imbalance=imbalance(bid_depth, ask_depth),
        message_count=book.message_count,
        messages_per_second=book.messages_per_second(),
        last_event_time=book.last_event_time,
        connection_status=book.connection_status,
    )
