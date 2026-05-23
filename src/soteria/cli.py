"""Command line interface for Soteria."""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Sequence
from pathlib import Path

from rich.console import Console

from soteria.app import watch_market
from soteria.collector import collect_features
from soteria.config import DEFAULT_LEVELS, DEFAULT_MODEL_PATH, DEFAULT_PRODUCT, SUPPORTED_PRODUCTS
from soteria.ml import train_model


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level command parser."""

    parser = argparse.ArgumentParser(
        prog="soteria",
        description="Public Coinbase market-depth monitoring and stress classification.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    watch = commands.add_parser("watch", help="Watch a live public level2 order book.")
    watch.add_argument("product", nargs="?", default=DEFAULT_PRODUCT, choices=SUPPORTED_PRODUCTS)
    watch.add_argument("--levels", type=int, default=DEFAULT_LEVELS)
    watch.add_argument("--raw", action="store_true", help="Print raw WebSocket payloads.")
    watch.add_argument("--ml", action="store_true", help="Enable trained stress classification.")
    watch.add_argument("--model", type=Path, default=DEFAULT_MODEL_PATH)

    collect = commands.add_parser("collect", help="Collect rolling public-market features to CSV.")
    collect.add_argument("product", nargs="?", default=DEFAULT_PRODUCT, choices=SUPPORTED_PRODUCTS)
    collect.add_argument("--seconds", type=int, required=True)
    collect.add_argument("--out", type=Path, required=True)

    train = commands.add_parser("train", help="Train a Keras market-stress classifier.")
    train.add_argument("--input", type=Path, required=True)
    train.add_argument("--model", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the selected Soteria command."""

    args = build_parser().parse_args(argv)
    console = Console(stderr=True)
    try:
        if args.command == "watch":
            if args.levels <= 0:
                raise ValueError("--levels must be positive.")
            if args.raw and args.ml:
                raise ValueError("--raw and --ml cannot be used together.")
            asyncio.run(
                watch_market(
                    product_id=args.product,
                    levels=args.levels,
                    raw=args.raw,
                    use_ml=args.ml,
                    model_path=args.model,
                )
            )
        elif args.command == "collect":
            rows = asyncio.run(collect_features(args.product, args.seconds, args.out))
            console.print(f"Collected {rows} feature rows in {args.out}.")
        elif args.command == "train":
            train_model(args.input, args.model)
            console.print(f"Saved market-stress model to {args.model}.")
    except KeyboardInterrupt:
        console.print("Stopped.")
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        return 2
    return 0
