from decimal import Decimal

from soteria.models import BookUpdate, Level2Event
from soteria.orderbook import OrderBook


def event(kind: str, *updates: BookUpdate) -> Level2Event:
    return Level2Event(kind=kind, product_id="BTC-USD", updates=updates)  # type: ignore[arg-type]


def test_apply_snapshot_and_sort_top_levels() -> None:
    book = OrderBook("BTC-USD")
    book.apply_event(
        event(
            "snapshot",
            BookUpdate("bid", Decimal("100"), Decimal("1.0")),
            BookUpdate("bid", Decimal("101"), Decimal("2.0")),
            BookUpdate("ask", Decimal("103"), Decimal("1.5")),
            BookUpdate("ask", Decimal("102"), Decimal("3.0")),
        )
    )

    assert [level.price for level in book.top_bids(2)] == [Decimal("101"), Decimal("100")]
    assert [level.price for level in book.top_asks(2)] == [Decimal("102"), Decimal("103")]
    assert book.best_bid().price == Decimal("101")  # type: ignore[union-attr]
    assert book.best_ask().price == Decimal("102")  # type: ignore[union-attr]


def test_updates_are_absolute_quantities() -> None:
    book = OrderBook("BTC-USD")
    book.apply_event(event("snapshot", BookUpdate("bid", Decimal("100"), Decimal("2"))))
    book.apply_event(event("update", BookUpdate("bid", Decimal("100"), Decimal("0.5"))))

    assert book.bids[Decimal("100")] == Decimal("0.5")


def test_zero_quantity_removes_price_level() -> None:
    book = OrderBook("BTC-USD")
    book.apply_event(event("snapshot", BookUpdate("ask", Decimal("102"), Decimal("2"))))
    book.apply_event(event("update", BookUpdate("ask", Decimal("102"), Decimal("0"))))

    assert book.top_asks(1) == ()
