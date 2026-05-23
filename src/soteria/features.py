"""Rolling numerical features computed from order-book state."""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from math import log
from statistics import pstdev

from soteria.metrics import calculate_metrics
from soteria.models import FeatureVector
from soteria.orderbook import OrderBook

ZERO = Decimal("0")


class FeatureEngine:
    """Build model-ready features while retaining a short mid-price history."""

    def __init__(self, history_seconds: int = 35) -> None:
        self.history_seconds = history_seconds
        self._mid_prices: deque[tuple[datetime, Decimal]] = deque()

    def build(self, book: OrderBook, timestamp: datetime | None = None) -> FeatureVector:
        """Capture one feature row from the current order-book state."""

        now = timestamp or datetime.now(UTC)
        metrics_5 = calculate_metrics(book, levels=5)
        metrics_10 = calculate_metrics(book, levels=10)
        mid_price = metrics_10.mid_price or ZERO
        self._add_mid_price(now, mid_price)

        spread = metrics_10.spread or ZERO
        spread_bps = spread / mid_price * Decimal("10000") if mid_price else ZERO
        bid_level = book.best_bid()
        ask_level = book.best_ask()
        values = {
            "spread": float(spread),
            "mid_price": float(mid_price),
            "spread_bps": float(spread_bps),
            "top_5_bid_depth": float(metrics_5.top_n_bid_depth),
            "top_5_ask_depth": float(metrics_5.top_n_ask_depth),
            "top_10_bid_depth": float(metrics_10.top_n_bid_depth),
            "top_10_ask_depth": float(metrics_10.top_n_ask_depth),
            "top_5_imbalance": float(metrics_5.top_n_imbalance),
            "top_10_imbalance": float(metrics_10.top_n_imbalance),
            "best_bid_size": float(bid_level.quantity if bid_level else ZERO),
            "best_ask_size": float(ask_level.quantity if ask_level else ZERO),
            "message_rate": metrics_10.messages_per_second,
            "mid_price_return_1s": self._price_return(now, mid_price, seconds=1),
            "mid_price_return_5s": self._price_return(now, mid_price, seconds=5),
            "rolling_volatility_10s": self._rolling_volatility(now, seconds=10),
            "rolling_volatility_30s": self._rolling_volatility(now, seconds=30),
        }
        return FeatureVector(timestamp=now, product_id=book.product_id, values=values)

    def _add_mid_price(self, timestamp: datetime, mid_price: Decimal) -> None:
        if mid_price:
            self._mid_prices.append((timestamp, mid_price))
        cutoff = timestamp - timedelta(seconds=self.history_seconds)
        while self._mid_prices and self._mid_prices[0][0] < cutoff:
            self._mid_prices.popleft()

    def _price_return(self, now: datetime, current: Decimal, seconds: int) -> float:
        if not current:
            return 0.0
        cutoff = now - timedelta(seconds=seconds)
        previous = next(
            (price for timestamp, price in reversed(self._mid_prices) if timestamp <= cutoff),
            None,
        )
        if previous is None or not previous:
            return 0.0
        return float((current - previous) / previous)

    def _rolling_volatility(self, now: datetime, seconds: int) -> float:
        cutoff = now - timedelta(seconds=seconds)
        prices = [float(price) for timestamp, price in self._mid_prices if timestamp >= cutoff]
        if len(prices) < 3:
            return 0.0
        returns = [
            log(current / previous) for previous, current in zip(prices, prices[1:], strict=False)
        ]
        return pstdev(returns) if len(returns) > 1 else 0.0
