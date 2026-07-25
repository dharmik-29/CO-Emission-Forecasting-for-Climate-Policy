"""
arima_model.py
==============
Step 5a: the statistical baseline (ARIMA).

ARIMA predicts the future by extending patterns in the past. It is the
interpretable, lightweight baseline every ML model must beat. We pick the
(p, d, q) orders automatically using the AIC score (lower = better fit).
"""

from __future__ import annotations

import warnings

import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller

from src.models.evaluate import metrics

warnings.filterwarnings("ignore")  # hide statsmodels convergence chatter


def adf_test(series: pd.Series) -> float:
    """Augmented Dickey-Fuller stationarity test. Returns the p-value.
    p < 0.05 => stationary; otherwise ARIMA needs differencing (the 'd')."""
    stat, pvalue, *_ = adfuller(series.dropna())
    verdict = "stationary" if pvalue < 0.05 else "non-stationary (needs differencing)"
    print(f"  ADF p-value = {pvalue:.4f} -> {verdict}")
    return pvalue


def fit_and_forecast(train: pd.Series, test: pd.Series) -> tuple[pd.Series, tuple, dict]:
    """Grid-search a small ARIMA space by AIC, then forecast the test window."""
    best_aic, best_order, best_fit = float("inf"), None, None
    for p in (1, 2):
        for q in (1, 2):
            try:
                fit = ARIMA(train, order=(p, 1, q)).fit()
                if fit.aic < best_aic:
                    best_aic, best_order, best_fit = fit.aic, (p, 1, q), fit
            except Exception:  # noqa: BLE001  some orders fail to converge
                continue

    print(f"  selected ARIMA{best_order} by AIC ({best_aic:.1f})")
    forecast = best_fit.forecast(steps=len(test))
    forecast.index = test.index
    result = metrics(test.values, forecast.values, f"ARIMA{best_order}")
    return forecast, best_order, result
