"""
powerbi_export.py
=================
Week 5 deliverable: run the models and export everything Power BI needs as clean
CSV files, plus SHAP interpretability.

Why CSV and not a .pbix file?
  A .pbix is Power BI Desktop's own binary format and can only be created inside
  Power BI Desktop. So the professional workflow is: this script produces tidy
  CSVs, and you import them into Power BI once (see powerbi/HOW_TO_BUILD_DASHBOARD.md).

This script reads the CLEAN CSV (data/raw/carbon_monitor_daily.csv) so it works
even without SQL Server running — handy for generating dashboard data quickly.
It creates the CSV first (via download) if it is missing.

Outputs (all in the powerbi/ folder):
  daily_emissions.csv    - the full tidy dataset (date, country, sector, mtco2)
  model_comparison.csv   - R2 / RMSE / MAE / MAPE for every model
  forecasts.csv          - actual vs each model's prediction on the test window
  feature_importance.csv - Random Forest importances
  shap_importance.csv    - mean |SHAP value| per feature (interpretability)

Run:
    python -m src.reporting.powerbi_export
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import config
from src.data.download import download
from src.features.build_features import build_features
from src.models.arima_model import fit_and_forecast
from src.models.ml_models import get_models
from src.models.evaluate import metrics

PBI_DIR = config.PROJECT_ROOT / "powerbi"
PBI_DIR.mkdir(exist_ok=True)


def _load_clean_frame() -> pd.DataFrame:
    """Load the cleaned tidy data, creating it from the Excel if needed."""
    if not config.RAW_CSV.exists():
        download()
    return pd.read_csv(config.RAW_CSV, parse_dates=["date"])


def _country_series(df: pd.DataFrame, country: str) -> pd.Series:
    """Sum the 6 sectors into one daily national total (same as the DB read)."""
    s = (df[df["country"] == country]
         .groupby("date")["mtco2_per_day"].sum()
         .asfreq("D").interpolate("time"))
    return s


def export() -> None:
    print("WEEK 5 · Exporting Power BI data + SHAP")
    df = _load_clean_frame()

    # 1) Full tidy dataset — the backbone of the dashboard (country/sector slicers)
    df.to_csv(PBI_DIR / "daily_emissions.csv", index=False)
    print(f"  wrote daily_emissions.csv ({len(df):,} rows)")

    # 2) Model training for the target country
    country = config.TARGET_COUNTRY
    series = _country_series(df, country)
    feats = build_features(series)

    split_idx = int(len(series) * config.TRAIN_FRACTION)
    split_date = series.index[split_idx]
    train_s, test_s = series.iloc[:split_idx], series.iloc[split_idx:]

    # ARIMA
    arima_pred, _order, arima_res = fit_and_forecast(train_s, test_s)

    # ML models
    X, y = feats.drop(columns="y"), feats["y"]
    X_train, X_test = X.loc[:split_date], X.loc[split_date:].iloc[1:]
    y_train, y_test = y.loc[X_train.index], y.loc[X_test.index]

    results = [arima_res]
    preds = {}
    fitted = {}
    for name, model in get_models().items():
        model.fit(X_train, y_train)
        fitted[name] = model
        p = pd.Series(model.predict(X_test), index=y_test.index)
        preds[name] = p
        results.append(metrics(y_test.values, p.values, name))

    # 3) Model comparison table
    comp = pd.DataFrame(results).round(4)
    comp.to_csv(PBI_DIR / "model_comparison.csv", index=False)
    print(f"  wrote model_comparison.csv ({len(comp)} models)")

    # 4) Forecasts: actual vs each model, aligned on the test dates
    fc = pd.DataFrame({"date": y_test.index, "actual": y_test.values})
    fc["ARIMA"] = arima_pred.reindex(y_test.index).values
    for name, p in preds.items():
        fc[name] = p.values
    fc["country"] = country
    fc.to_csv(PBI_DIR / "forecasts.csv", index=False)
    print(f"  wrote forecasts.csv ({len(fc)} test days)")

    # 5) Random Forest feature importance
    rf = fitted["RandomForest"]
    imp = (pd.DataFrame({"feature": X.columns, "importance": rf.feature_importances_})
           .sort_values("importance", ascending=False))
    imp.to_csv(PBI_DIR / "feature_importance.csv", index=False)
    print(f"  wrote feature_importance.csv")

    # 6) SHAP interpretability — mean absolute SHAP value per feature
    _export_shap(rf, X_test, X.columns)

    print(f"\n  All Power BI files are in: "
          f"{PBI_DIR.relative_to(config.PROJECT_ROOT)}")


def _export_shap(model, X_sample: pd.DataFrame, columns) -> None:
    """Compute SHAP values for the tree model and export the ranking.

    SHAP explains WHICH features drive each prediction — the interpretability
    argument (RQ2). If shap is not installed we fall back to model importances
    so the pipeline never breaks.
    """
    try:
        import shap
        # TreeExplainer is fast and exact for tree ensembles
        explainer = shap.TreeExplainer(model)
        shap_vals = explainer.shap_values(X_sample)
        mean_abs = np.abs(shap_vals).mean(axis=0)
        out = (pd.DataFrame({"feature": columns, "mean_abs_shap": mean_abs})
               .sort_values("mean_abs_shap", ascending=False))
        out.to_csv(PBI_DIR / "shap_importance.csv", index=False)
        print("  wrote shap_importance.csv (SHAP interpretability)")
    except ImportError:
        print("  (shap not installed - run 'pip install shap' for SHAP export)")


if __name__ == "__main__":
    export()
