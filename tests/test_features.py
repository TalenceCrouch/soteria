from datetime import UTC, datetime, timedelta
from decimal import Decimal

from soteria.config import FEATURE_NAMES
from soteria.features import FeatureEngine
from soteria.models import BookUpdate, Level2Event
from soteria.orderbook import OrderBook


def set_book(book: OrderBook, bid: str, ask: str) -> None:
    book.apply_event(
        Level2Event(
            kind="snapshot",
            product_id="BTC-USD",
            updates=(
                BookUpdate("bid", Decimal(bid), Decimal("2")),
                BookUpdate("ask", Decimal(ask), Decimal("1")),
            ),
        )
    )


def test_feature_vector_generation_includes_returns_and_depth() -> None:
    book = OrderBook("BTC-USD")
    engine = FeatureEngine()
    start = datetime(2026, 1, 1, tzinfo=UTC)

    set_book(book, "99", "101")
    engine.build(book, timestamp=start)
    set_book(book, "100", "102")
    row = engine.build(book, timestamp=start + timedelta(seconds=1))

    assert tuple(row.values) == FEATURE_NAMES
    assert row.values["spread"] == 2.0
    assert row.values["mid_price"] == 101.0
    assert row.values["top_5_imbalance"] > 0
    assert row.values["mid_price_return_1s"] > 0


def test_rolling_volatility_becomes_positive_for_changing_prices() -> None:
    book = OrderBook("BTC-USD")
    engine = FeatureEngine()
    start = datetime(2026, 1, 1, tzinfo=UTC)

    for offset, (bid, ask) in enumerate([("99", "101"), ("100", "102"), ("102", "104")]):
        set_book(book, bid, ask)
        row = engine.build(book, timestamp=start + timedelta(seconds=offset))

    assert row.values["rolling_volatility_10s"] > 0
