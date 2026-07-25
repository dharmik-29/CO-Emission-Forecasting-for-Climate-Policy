"""
test_pipeline.py
================
Basic unit tests for the pipeline. Run with:  pytest

These are intentionally lightweight — they prove the core data-shaping logic is
correct without needing the full model training run.
"""

import numpy as np
import pandas as pd

from src.data.download import _make_synthetic
from src.data.etl import transform
from src.features.build_features import build_features


def test_synthetic_shape():
    """Fallback synthetic data has the right columns and no missing values."""
    df = _make_synthetic(n_days=100)
    assert list(df.columns) == ["date", "country", "sector", "mtco2_per_day"]
    # 100 days x 6 sectors for one country
    assert len(df) == 100 * 6
    assert df["mtco2_per_day"].notna().all()


def test_transform_removes_duplicates():
    """ETL transform drops duplicate (date, country, sector) rows."""
    df = _make_synthetic(n_days=10)
    doubled = pd.concat([df, df], ignore_index=True)   # doubled rows, half unique
    cleaned = transform(doubled)
    assert len(cleaned) == 10 * 6


def test_features_have_no_nans():
    """Feature engineering drops warm-up rows so there are no NaNs left."""
    idx = pd.date_range("2020-01-01", periods=200, freq="D")
    series = pd.Series(np.arange(200, dtype=float), index=idx)
    feats = build_features(series)
    assert feats.notna().all().all()
    assert "lag_7" in feats.columns
