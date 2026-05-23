from decimal import Decimal

from soteria.coinbase import parse_message, subscription_messages


def test_parse_level2_snapshot_and_update_fields() -> None:
    message = {
        "channel": "l2_data",
        "events": [
            {
                "type": "update",
                "product_id": "BTC-USD",
                "updates": [
                    {
                        "side": "offer",
                        "event_time": "2026-01-01T00:00:00Z",
                        "price_level": "102.50",
                        "new_quantity": "0",
                    }
                ],
            }
        ],
    }

    events = parse_message(message)

    assert events[0].kind == "update"
    assert events[0].updates[0].side == "ask"
    assert events[0].updates[0].price == Decimal("102.50")
    assert events[0].updates[0].quantity == Decimal("0")


def test_unknown_or_invalid_messages_are_ignored_safely() -> None:
    assert parse_message('{"channel": "heartbeats", "events": []}') == ()
    assert parse_message("{not-json") == ()


def test_public_subscriptions_never_include_credentials() -> None:
    subscriptions = subscription_messages("BTC-USD")

    assert subscriptions[0]["channel"] == "level2"
    assert all("jwt" not in message for message in subscriptions)
