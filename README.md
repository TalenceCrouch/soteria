# Soteria

Soteria is an asynchronous Python terminal application for watching public Coinbase
Advanced Trade market data. It streams the `level2` WebSocket channel, maintains a
Decimal-based order book, computes market-depth and short-horizon volatility features,
and can classify market stress with a small TensorFlow/Keras model.

Soteria exists as an understandable market-data analytics project: it makes order-book
state, depth imbalance, and live volatility visible without introducing trading
execution or private account access.

## Safety And Scope

Soteria is **not a trading bot**. It does not place orders, access private Coinbase
account/order APIs, require API secrets, or recommend buying or selling. Its ML output
is a market-stress / volatility classification only and is not financial advice.

Intentionally out of scope:

- Order placement, portfolio management, or exchange account authentication.
- Buy/sell signals, profit claims, or financial guarantees.
- Web dashboards, cloud services, databases, event platforms, or agent frameworks.

## Requirements

- Python 3.11 or newer
- Network access to the public Coinbase Advanced Trade market-data WebSocket for live use

Coinbase documents the public market-data endpoint and `level2` schema in its
[Advanced Trade WebSocket documentation](https://docs.cdp.coinbase.com/coinbase-app/advanced-trade-apis/websocket/websocket-overview).
The feed sends absolute `new_quantity` values; a quantity of `"0"` removes a price
level. Soteria subscribes only to the public `level2` and `heartbeats` channels.

## Install

Create and activate a virtual environment, then install live monitoring support:

```bash
python -m venv .venv
python -m pip install -e .
```

Install machine learning support when training a model or using `--ml`:

```bash
python -m pip install -e ".[ml]"
```

For development and tests, including TensorFlow and Ruff:

```bash
python -m pip install -e ".[dev]"
```

TensorFlow is imported only by ML commands, so basic public market monitoring does not
need the larger ML dependency.

## Watch Live Data

Watch the default depth view for Bitcoin:

```bash
soteria watch BTC-USD
```

Choose how many levels appear in the Rich order-book table:

```bash
soteria watch BTC-USD --levels 10
```

Inspect unprocessed public WebSocket payloads:

```bash
soteria watch BTC-USD --raw
```

`ETH-USD` is also supported:

```bash
soteria watch ETH-USD
```

The display includes connection status, event time, message rate, best bid and ask,
spread, mid price, top-10 depth, imbalance, and a `calm`, `active`, or `stressed`
market-state description.

## Collect Features

Collect event-driven feature rows from the live public order book:

```bash
soteria collect BTC-USD --seconds 300 --out data/btc_usd_features.csv
```

Each CSV row contains depth, imbalance, top-of-book size, message rate, mid-price
returns, and trailing volatility measures. Collection writes no orders and requires no
credentials.

## Train The Stress Model

Train a compact Keras binary classifier on a collected CSV:

```bash
soteria train --input data/btc_usd_features.csv --model artifacts/stress_model.keras
```

Labeling is deliberately simple and documented in `soteria.ml`: a feature row is
labelled `stress = 1` when a soon-following row within the next 10 collected rows has
`rolling_volatility_10s` above `0.0015`; otherwise it is labelled `stress = 0`.
Because collection is event-driven, this is a short forward-looking volatility
heuristic, not a directional forecast and not a trade signal.

## Watch With ML

After a model has been trained, display its stress probability:

```bash
soteria watch BTC-USD --ml --model artifacts/stress_model.keras
```

When `--model` is omitted, `--ml` looks for `artifacts/stress_model.keras`.
The probability describes estimated short-term market stress only.

## Development

Run formatting, linting, and tests:

```bash
ruff format .
ruff check .
pytest
```

The tests exercise snapshots, absolute level updates, level removal, depth metrics,
feature creation, stress labels, model prediction shape, and defensive Coinbase
message parsing.
