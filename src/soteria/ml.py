"""TensorFlow/Keras market-stress classification helpers."""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from soteria.config import FEATURE_NAMES, LABEL_FUTURE_ROWS, LABEL_VOLATILITY_THRESHOLD

if TYPE_CHECKING:
    from tensorflow import keras


def _keras() -> Any:
    """Import TensorFlow only for commands that actually use ML."""

    try:
        from tensorflow import keras
    except ImportError as exc:
        raise RuntimeError(
            "TensorFlow is required for ML commands. Install Soteria with the 'ml' extra."
        ) from exc
    return keras


def build_model(input_dim: int) -> keras.Model:
    """Build a compact binary classifier for near-term market stress."""

    keras_module = _keras()
    model = keras_module.Sequential(
        [
            keras_module.Input(shape=(input_dim,)),
            keras_module.layers.Normalization(name="normalize"),
            keras_module.layers.Dense(16, activation="relu"),
            keras_module.layers.Dropout(0.1),
            keras_module.layers.Dense(8, activation="relu"),
            keras_module.layers.Dense(1, activation="sigmoid"),
        ],
        name="soteria_stress_classifier",
    )
    model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
    return model


def generate_stress_labels(
    rows: Sequence[Mapping[str, float | str]],
    future_rows: int = LABEL_FUTURE_ROWS,
    threshold: float = LABEL_VOLATILITY_THRESHOLD,
) -> list[int]:
    """Label a row stressed when soon-following 10-second volatility is high.

    Collection is event-driven, so ``future_rows`` is a deliberately simple
    short horizon rather than a prediction of price direction or a trade signal.
    """

    labels: list[int] = []
    for index in range(len(rows)):
        future = rows[index + 1 : index + 1 + future_rows]
        future_volatilities = [float(row["rolling_volatility_10s"]) for row in future]
        labels.append(int(bool(future_volatilities) and max(future_volatilities) > threshold))
    return labels


def _read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", newline="", encoding="utf-8") as csv_file:
        return list(csv.DictReader(csv_file))


def train_model(csv_path: Path, model_path: Path) -> None:
    """Train and save a stress classifier from collected Soteria feature rows."""

    import numpy as np

    rows = _read_rows(csv_path)
    if len(rows) < 2:
        raise ValueError("Training needs at least two collected feature rows.")
    missing = [name for name in FEATURE_NAMES if name not in rows[0]]
    if missing:
        raise ValueError(f"Training data is missing features: {', '.join(missing)}")

    features = np.asarray(
        [[float(row[name]) for name in FEATURE_NAMES] for row in rows],
        dtype=np.float32,
    )
    labels = np.asarray(generate_stress_labels(rows), dtype=np.float32)

    model = build_model(input_dim=len(FEATURE_NAMES))
    model.get_layer("normalize").adapt(features)
    validation_split = 0.2 if len(rows) >= 10 else 0.0
    model.fit(
        features,
        labels,
        epochs=20,
        batch_size=min(32, len(rows)),
        validation_split=validation_split,
        verbose=0,
    )
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model.save(model_path)


def load_model(model_path: Path) -> keras.Model:
    """Load a saved Keras market-stress classifier."""

    return _keras().models.load_model(model_path)


def predict_stress(model: keras.Model, feature_vector: Sequence[float]) -> float:
    """Return a bounded stress probability, where higher means more volatile."""

    import numpy as np

    inputs = np.asarray([feature_vector], dtype=np.float32)
    probability = float(model.predict(inputs, verbose=0)[0][0])
    return max(0.0, min(1.0, probability))
