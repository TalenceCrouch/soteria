"""Async application orchestration for live Soteria monitoring."""

from __future__ import annotations

import asyncio
from pathlib import Path

from rich.console import Console
from rich.live import Live
from websockets.exceptions import ConnectionClosed

from soteria.coinbase import CoinbaseMarketDataClient, parse_message
from soteria.config import FEATURE_NAMES
from soteria.features import FeatureEngine, FeatureVector
from soteria.ml import load_model, predict_stress
from soteria.orderbook import OrderBook
from soteria.render import TerminalRenderer


async def watch_market(
    product_id: str,
    levels: int,
    raw: bool,
    use_ml: bool,
    model_path: Path,
) -> None:
    """Continuously stream and render public Coinbase level2 market data."""

    if raw:
        await _watch_raw(product_id)
        return
    if use_ml and not model_path.exists():
        raise FileNotFoundError(
            f"No trained model found at {model_path}. Run 'soteria train' first."
        )

    model = load_model(model_path) if use_ml else None
    book = OrderBook(product_id)
    feature_engine = FeatureEngine()
    renderer = TerminalRenderer(product_id=product_id, levels=levels)
    client = CoinbaseMarketDataClient()
    console = Console()
    current_features: FeatureVector | None = None
    probability: float | None = None

    book.connection_status = "connecting"
    with Live(renderer.render(book), console=console, refresh_per_second=4) as live:
        while True:
            try:
                async for raw_message in client.messages(product_id):
                    for event in parse_message(raw_message):
                        book.apply_event(event)
                        current_features = feature_engine.build(book)
                        if model is not None:
                            feature_values = [
                                current_features.values[name] for name in FEATURE_NAMES
                            ]
                            probability = predict_stress(model, feature_values)
                        live.update(renderer.render(book, current_features, probability))
            except asyncio.CancelledError:
                raise
            except (ConnectionClosed, OSError):
                book.connection_status = "reconnecting"
                live.update(renderer.render(book, current_features, probability))
                await asyncio.sleep(1)


async def _watch_raw(product_id: str) -> None:
    """Print unmodified public messages, reconnecting after transient errors."""

    console = Console()
    client = CoinbaseMarketDataClient()
    while True:
        try:
            async for raw_message in client.messages(product_id):
                console.print(raw_message)
        except asyncio.CancelledError:
            raise
        except (ConnectionClosed, OSError):
            console.print("[yellow]Connection interrupted; retrying...[/yellow]")
            await asyncio.sleep(1)
