from decimal import Decimal

from soteria.metrics import calculate_metrics, imbalance
from soteria.models import BookUpdate, Level2Event
from soteria.orderbook import OrderBook


def populated_book() -> OrderBook:
    book = OrderBook("BTC-USD")
    book.apply_event(
        Level2Event(
            kind="snapshot",
            product_id="BTC-USD",
            updates=(
                BookUpdate("bid", Decimal("100"), Decimal("3")),
                BookUpdate("bid", Decimal("99"), Decimal("1")),
                BookUpdate("ask", Decimal("102"), Decimal("2")),
                BookUpdate("ask", Decimal("103"), Decimal("2")),
            ),
        )
    )
    return book


def test_best_prices_spread_and_mid_price() -> None:
    metrics = calculate_metrics(populated_book(), levels=10)

    assert metrics.best_bid == Decimal("100")
    assert metrics.best_ask == Decimal("102")
    assert metrics.spread == Decimal("2")
    assert metrics.mid_price == Decimal("101")


def test_depth_and_imbalance() -> None:
    metrics = calculate_metrics(populated_book(), levels=1)

    assert metrics.top_n_bid_depth == Decimal("3")
    assert metrics.top_n_ask_depth == Decimal("2")
    assert metrics.top_n_imbalance == Decimal("0.2")
    assert imbalance(Decimal("0"), Decimal("0")) == Decimal("0")


def test_empty_order_book_has_no_prices_and_zero_depth() -> None:
    metrics = calculate_metrics(OrderBook("BTC-USD"), levels=10)

    assert metrics.best_bid is None
    assert metrics.best_ask is None
    assert metrics.spread is None
    assert metrics.mid_price is None
    assert metrics.top_n_bid_depth == Decimal("0")
    assert metrics.top_n_ask_depth == Decimal("0")
    assert metrics.top_n_imbalance == Decimal("0")
