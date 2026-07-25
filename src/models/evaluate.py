"""
evaluate.py
===========
Shared evaluation metrics used by every model, so the comparison is fair.

Metrics (from slide 11):
  R2   - coefficient of determination (higher is better, 1.0 = perfect)
  RMSE - root mean squared error       (lower is better, penalises big misses)
  MAE  - mean absolute error           (lower is better, average miss)
  MAPE - mean absolute percentage error(lower is better, error as a %)
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (mean_absolute_error,
                             mean_absolute_percentage_error,
                             mean_squared_error, r2_score)


def metrics(y_true, y_pred, name: str) -> dict:
    """Return a dict of the four standard metrics for one model."""
    return {
        "model": name,
        "R2": r2_score(y_true, y_pred),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAE": mean_absolute_error(y_true, y_pred),
        "MAPE": mean_absolute_percentage_error(y_true, y_pred) * 100,
    }
