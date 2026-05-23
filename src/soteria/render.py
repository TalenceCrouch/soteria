"""Rich terminal rendering for live market monitoring."""

from __future__ import annotations

from decimal import Decimal

from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table

from soteria.features import FeatureVector
from soteria.metrics import calculate_metrics
from soteria.orderbook import OrderBook


def _decimal(value: Decimal | None, places: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:,.{places}f}"


def market_state(probability: float | None, features: FeatureVector | None) -> str:
    """Describe market stress, never a trading recommendation."""

    if probability is not None:
        if probability >= 0.7:
            return "stressed"
        if probability >= 0.35:
            return "active"
        return "calm"
    volatility = features.values["rolling_volatility_10s"] if features else 0.0
    if volatility >= 0.002:
        return "stressed"
    if volatility >= 0.0008:
        return "active"
    return "calm"


class TerminalRenderer:
    """Produce a Rich dashboard from the latest public market state."""

    def __init__(self, product_id: str, levels: int) -> None:
        self.product_id = product_id
        self.levels = levels

    def render(
        self,
        book: OrderBook,
        features: FeatureVector | None = None,
        stress_probability: float | None = None,
    ) -> RenderableType:
        """Build the current dashboard view."""

        metrics = calculate_metrics(book, levels=10)
        summary = Table.grid(expand=True)
        summary.add_column(style="bold cyan")
        summary.add_column()
        summary.add_column(style="bold cyan")
        summary.add_column()
        summary.add_row("Product", self.product_id, "Connection", metrics.connection_status)
        summary.add_row(
            "Last event",
            metrics.last_event_time.isoformat() if metrics.last_event_time else "-",
            "Messages/sec",
            f"{metrics.messages_per_second:.1f}",
        )
        summary.add_row(
            "Best bid", _decimal(metrics.best_bid), "Best ask", _decimal(metrics.best_ask)
        )
        summary.add_row(
            "Spread", _decimal(metrics.spread), "Mid price", _decimal(metrics.mid_price)
        )
        summary.add_row(
            "Top 10 bid depth",
            _decimal(metrics.top_n_bid_depth, 6),
            "Top 10 ask depth",
            _decimal(metrics.top_n_ask_depth, 6),
        )
        summary.add_row(
            "Top 10 imbalance",
            f"{float(metrics.top_n_imbalance):+.3f}",
            "Market state",
            market_state(stress_probability, features),
        )
        if stress_probability is not None:
            summary.add_row(
                "ML stress probability",
                f"{stress_probability:.1%}",
                "Interpretation",
                "volatility classification only",
            )

        order_book = Table(title=f"Order Book - Top {self.levels}", expand=True)
        order_book.add_column("Bid qty", justify="right", style="green")
        order_book.add_column("Bid price", justify="right", style="green")
        order_book.add_column("Ask price", justify="right", style="red")
        order_book.add_column("Ask qty", justify="right", style="red")
        bids = book.top_bids(self.levels)
        asks = book.top_asks(self.levels)
        for index in range(max(len(bids), len(asks), self.levels)):
            bid = bids[index] if index < len(bids) else None
            ask = asks[index] if index < len(asks) else None
            order_book.add_row(
                _decimal(bid.quantity, 6) if bid else "",
                _decimal(bid.price) if bid else "",
                _decimal(ask.price) if ask else "",
                _decimal(ask.quantity, 6) if ask else "",
            )
        return Panel(Group(summary, order_book), title="Soteria", border_style="blue")
