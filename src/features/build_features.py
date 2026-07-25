"""
build_features.py
=================
Step 4 of the pipeline: turn the raw daily series into a feature table for the
machine-learning models.

Time-series models can't just see today's date — they need *memory* and
*context*. We give them:
  - lag features   : the value 1, 7 and 30 days ago
  - rolling stats  : 7-day rolling mean and standard deviation
  - calendar flags : day of week, month

These come straight from the methodology on slides 10-11 of the presentation.
The daily series is read out of SQL Server (summing the 6 sectors per day).
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src import config
from src.data.db import get_engine


def load_series_from_db(country: str | None = None) -> pd.Series:
    """Read the total daily emissions for ONE country out of SQL Server.

    We sum the 6 sectors together to get a single national daily total, then
    force a continuous daily frequency and fill any gaps.
    """
    country = country or config.TARGET_COUNTRY
    engine = get_engine()

    # Parameterised query (:country) — safe from SQL injection and clean.
    sql = text(
        "SELECT date, SUM(mtco2_per_day) AS y "
        "FROM daily_emissions WHERE country = :country "
        "GROUP BY date ORDER BY date"
    )
    with engine.connect() as conn:
        df = pd.read_sql_query(sql, conn, params={"country": country},
                               parse_dates=["date"])

    if df.empty:
        raise ValueError(f"No rows found for country '{country}'. "
                         f"Check config.TARGET_COUNTRY spelling.")

    series = df.set_index("date")["y"].asfreq("D")
    # Fill any gaps introduced by asfreq so downstream code never sees NaNs
    return series.interpolate(method="time")


def build_features(series: pd.Series) -> pd.DataFrame:
    """Create the model-ready feature matrix (drops the warm-up rows with NaNs)."""
    df = pd.DataFrame({"y": series})
    for lag in config.LAGS:
        df[f"lag_{lag}"] = series.shift(lag)
    df["roll_mean_7"] = series.shift(1).rolling(7).mean()
    df["roll_std_7"] = series.shift(1).rolling(7).std()
    df["dayofweek"] = df.index.dayofweek
    df["month"] = df.index.month
    return df.dropna()


if __name__ == "__main__":
    s = load_series_from_db()
    feats = build_features(s)
    print(f"series: {len(s)} days -> features: {feats.shape[0]} rows, "
          f"{feats.shape[1] - 1} predictors")
    print(feats.head())
