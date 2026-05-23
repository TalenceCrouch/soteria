"""Feature collection from the public Coinbase level2 stream."""

from __future__ import annotations

import asyncio
import csv
from pathlib import Path

from soteria.coinbase import CoinbaseMarketDataClient, parse_message
from soteria.config import FEATURE_NAMES
from soteria.features import FeatureEngine
from soteria.orderbook import OrderBook


async def collect_features(product_id: str, seconds: int, out_path: Path) -> int:
    """Stream public data for a duration and write model-ready CSV feature rows."""

    if seconds <= 0:
        raise ValueError("Collection duration must be positive.")

    book = OrderBook(product_id)
    engine = FeatureEngine()
    client = CoinbaseMarketDataClient()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0

    with out_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["timestamp", "product_id", *FEATURE_NAMES])
        writer.writeheader()
        try:
            async with asyncio.timeout(seconds):
                async for raw_message in client.messages(product_id):
                    for event in parse_message(raw_message):
                        book.apply_event(event)
                        writer.writerow(engine.build(book).as_row())
                        row_count += 1
        except TimeoutError:
            pass
    return row_count
