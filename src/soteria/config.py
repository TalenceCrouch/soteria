"""Configuration constants used throughout Soteria."""

from pathlib import Path

COINBASE_MARKET_DATA_URL = "wss://advanced-trade-ws.coinbase.com"
DEFAULT_PRODUCT = "BTC-USD"
SUPPORTED_PRODUCTS = ("BTC-USD", "ETH-USD")
DEFAULT_LEVELS = 10
DEFAULT_MODEL_PATH = Path("artifacts/stress_model.keras")

FEATURE_NAMES = (
    "spread",
    "mid_price",
    "spread_bps",
    "top_5_bid_depth",
    "top_5_ask_depth",
    "top_10_bid_depth",
    "top_10_ask_depth",
    "top_5_imbalance",
    "top_10_imbalance",
    "best_bid_size",
    "best_ask_size",
    "message_rate",
    "mid_price_return_1s",
    "mid_price_return_5s",
    "rolling_volatility_10s",
    "rolling_volatility_30s",
)

LABEL_FUTURE_ROWS = 10
LABEL_VOLATILITY_THRESHOLD = 0.0015
