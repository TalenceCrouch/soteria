import pytest

from soteria.config import FEATURE_NAMES
from soteria.ml import build_model, generate_stress_labels, predict_stress


def test_label_generation_looks_forward_at_volatility() -> None:
    rows = [
        {"rolling_volatility_10s": 0.0001},
        {"rolling_volatility_10s": 0.0020},
        {"rolling_volatility_10s": 0.0002},
    ]

    assert generate_stress_labels(rows, future_rows=1, threshold=0.0015) == [1, 0, 0]


def test_model_builds_and_predicts_probability() -> None:
    pytest.importorskip("tensorflow")
    model = build_model(input_dim=len(FEATURE_NAMES))

    probability = predict_stress(model, [0.0] * len(FEATURE_NAMES))

    assert model.output_shape == (None, 1)
    assert 0.0 <= probability <= 1.0
