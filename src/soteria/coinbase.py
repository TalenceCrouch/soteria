"""Public Coinbase Advanced Trade WebSocket connectivity and message parsing."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Mapping
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from websockets import connect

from soteria.config import COINBASE_MARKET_DATA_URL
from soteria.models import BookSide, BookUpdate, Level2Event


def subscription_messages(product_id: str) -> tuple[dict[str, object], ...]:
    """Create public market-data subscriptions; no account API or token is used."""

    return (
        {"type": "subscribe", "product_ids": [product_id], "channel": "level2"},
        {"type": "subscribe", "channel": "heartbeats"},
    )


def _parse_event_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _parse_side(value: object) -> BookSide | None:
    if not isinstance(value, str):
        return None
    normalized = value.lower()
    if normalized in {"bid", "buy"}:
        return "bid"
    if normalized in {"ask", "offer", "sell"}:
        return "ask"
    return None


def _parse_update(payload: object) -> BookUpdate | None:
    if not isinstance(payload, Mapping):
        return None
    side = _parse_side(payload.get("side"))
    if side is None:
        return None
    try:
        price = Decimal(str(payload["price_level"]))
        quantity = Decimal(str(payload["new_quantity"]))
    except (InvalidOperation, KeyError):
        return None
    return BookUpdate(
        side=side,
        price=price,
        quantity=quantity,
        event_time=_parse_event_time(payload.get("event_time")),
    )


def parse_message(raw_message: str | Mapping[str, Any]) -> tuple[Level2Event, ...]:
    """Parse known level2 payloads and safely ignore other Coinbase messages."""

    try:
        message = json.loads(raw_message) if isinstance(raw_message, str) else raw_message
    except json.JSONDecodeError:
        return ()
    if not isinstance(message, Mapping) or message.get("channel") not in {"l2_data", "level2"}:
        return ()

    raw_events = message.get("events", [])
    if not isinstance(raw_events, list):
        return ()

    parsed_events: list[Level2Event] = []
    for raw_event in raw_events:
        if not isinstance(raw_event, Mapping):
            continue
        kind = raw_event.get("type")
        product_id = raw_event.get("product_id")
        if kind not in {"snapshot", "update"} or not isinstance(product_id, str):
            continue
        raw_updates = raw_event.get("updates", [])
        if not isinstance(raw_updates, list):
            continue
        updates = tuple(
            update for payload in raw_updates if (update := _parse_update(payload)) is not None
        )
        parsed_events.append(
            Level2Event(kind=kind, product_id=product_id, updates=updates)  # type: ignore[arg-type]
        )
    return tuple(parsed_events)


class CoinbaseMarketDataClient:
    """Streams public Coinbase market messages for one product."""

    def __init__(self, url: str = COINBASE_MARKET_DATA_URL) -> None:
        self.url = url

    async def messages(self, product_id: str) -> AsyncIterator[str]:
        """Yield raw public messages after subscribing to level2 and heartbeats."""

        async with connect(self.url, ping_interval=20, ping_timeout=20) as websocket:
            for subscription in subscription_messages(product_id):
                await websocket.send(json.dumps(subscription))
            async for raw_message in websocket:
                yield str(raw_message)
