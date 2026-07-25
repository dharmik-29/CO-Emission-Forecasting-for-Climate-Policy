"""
plots.py
========
Generates the figures saved to reports/figures/. Kept separate from the modeling
code so plotting never interferes with the analysis.
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")  # non-interactive backend: save files without a display
import matplotlib.pyplot as plt  # noqa: E402

from src import config  # noqa: E402

plt.rcParams["figure.figsize"] = (11, 4)
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.alpha"] = 0.3


def plot_series(series, filename="01_daily_series.png"):
    """Line chart of the full daily series."""
    ax = series.plot(color="teal", lw=0.9)
    ax.set(title="Daily CO2 emissions", ylabel="Mt CO2 / day", xlabel="")
    _save(filename)


def plot_forecasts(y_test, arima_pred, ml_preds, filename="02_forecasts.png"):
    """Overlay actual vs each model's forecast on the hold-out window."""
    fig, ax = plt.subplots()
    ax.plot(y_test.index, y_test.values, label="Actual", color="black", lw=1.4)
    ax.plot(arima_pred.index, arima_pred.values, label="ARIMA", ls="--", alpha=.8)
    for name, pred in ml_preds.items():
        ax.plot(pred.index, pred.values, label=name, alpha=.8)
    ax.set(title="Forecast vs actual (hold-out period)", ylabel="Mt CO2 / day")
    ax.legend()
    _save(filename)


def plot_importance(importance, filename="03_feature_importance.png"):
    """Horizontal bar chart of Random Forest feature importances."""
    ax = importance.sort_values().plot.barh(color="teal")
    ax.set(title="Random Forest feature importance", xlabel="importance")
    _save(filename)


def _save(filename: str) -> None:
    path = config.FIGURES_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  saved figure -> {path.relative_to(config.PROJECT_ROOT)}")
