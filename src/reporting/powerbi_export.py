"""
powerbi_export.py
=================
Runs the models for EVERY country and exports the CSVs used by the Power BI
dashboard and the Streamlit app, plus SHAP interpretability.

Two sets of files are written into powerbi/:

  Power BI (single target country, e.g. China) — keeps the dashboard simple:
    model_comparison.csv · forecasts.csv · feature_importance.csv · shap_importance.csv

  Streamlit app (ALL countries, with a 'country' column) — lets the app show
  forecasts for whichever country the user picks:
    model_comparison_all.csv · forecasts_all.csv · shap_all.csv

  daily_emissions.csv (all countries) is shared by both.

Reads the clean CSV (data/raw/carbon_monitor_daily.csv), creating it from the
Excel first if needed — so it works without SQL Server running.

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
    return (df[df["country"] == country]
            .groupby("date")["mtco2_per_day"].sum()
            .asfreq("D").interpolate("time"))


def _shap_ranking(model, X_sample: pd.DataFrame, columns) -> pd.DataFrame | None:
    """Mean absolute SHAP value per feature (interpretability). None if shap missing."""
    try:
        import shap
        explainer = shap.TreeExplainer(model)
        vals = explainer.shap_values(X_sample)
        return (pd.DataFrame({"feature": columns, "mean_abs_shap": np.abs(vals).mean(axis=0)})
                .sort_values("mean_abs_shap", ascending=False))
    except ImportError:
        return None


def _model_one_country(df: pd.DataFrame, country: str):
    """Train all models for one country. Returns (metrics_rows, forecast_df,
    importance_df, shap_df) — or None if the country has too little data."""
    series = _country_series(df, country)
    feats = build_features(series)
    if len(feats) < 60:
        return None

    split_idx = int(len(series) * config.TRAIN_FRACTION)
    split_date = series.index[split_idx]
    train_s, test_s = series.iloc[:split_idx], series.iloc[split_idx:]

    # ARIMA baseline
    arima_pred, _order, arima_res = fit_and_forecast(train_s, test_s)
    arima_res["country"] = country

    # ML models on the same chronological split
    X, y = feats.drop(columns="y"), feats["y"]
    X_train, X_test = X.loc[:split_date], X.loc[split_date:].iloc[1:]
    y_train, y_test = y.loc[X_train.index], y.loc[X_test.index]

    rows, preds, fitted = [arima_res], {}, {}
    for name, model in get_models().items():
        model.fit(X_train, y_train)
        fitted[name] = model
        p = pd.Series(model.predict(X_test), index=y_test.index)
        preds[name] = p
        r = metrics(y_test.values, p.values, name)
        r["country"] = country
        rows.append(r)

    # Forecast table (actual vs each model), tagged with the country
    fc = pd.DataFrame({"date": y_test.index, "actual": y_test.values})
    fc["ARIMA"] = arima_pred.reindex(y_test.index).values
    for name, p in preds.items():
        fc[name] = p.values
    fc["country"] = country

    # Feature importance + SHAP from the Random Forest
    rf = fitted["RandomForest"]
    imp = pd.DataFrame({"feature": X.columns,
                        "importance": rf.feature_importances_,
                        "country": country})
    shap_df = _shap_ranking(rf, X_test, X.columns)
    if shap_df is not None:
        shap_df["country"] = country

    return rows, fc, imp, shap_df


def export() -> None:
    print("Exporting dashboard + app data for ALL countries")
    df = _load_clean_frame()

    # Shared file: full tidy dataset (all countries)
    df.to_csv(PBI_DIR / "daily_emissions.csv", index=False)
    print(f"  wrote daily_emissions.csv ({len(df):,} rows)")

    all_rows, all_fc, all_imp, all_shap = [], [], [], []
    for country in config.SELECTED_COUNTRIES:
        result = _model_one_country(df, country)
        if result is None:
            print(f"  {country}: skipped (not enough data)")
            continue
        rows, fc, imp, shap_df = result
        all_rows.extend(rows)
        all_fc.append(fc)
        all_imp.append(imp)
        if shap_df is not None:
            all_shap.append(shap_df)
        print(f"  {country}: modelled")

    comp_all = pd.DataFrame(all_rows).round(4)
    fc_all = pd.concat(all_fc, ignore_index=True)
    imp_all = pd.concat(all_imp, ignore_index=True)

    # ---- ALL-country files (Streamlit app) ----
    comp_all.to_csv(PBI_DIR / "model_comparison_all.csv", index=False)
    fc_all.to_csv(PBI_DIR / "forecasts_all.csv", index=False)
    if all_shap:
        pd.concat(all_shap, ignore_index=True).to_csv(PBI_DIR / "shap_all.csv", index=False)

    # ---- Single-country files (Power BI dashboard) ----
    tc = config.TARGET_COUNTRY
    (comp_all[comp_all["country"] == tc].drop(columns="country")
        .to_csv(PBI_DIR / "model_comparison.csv", index=False))
    fc_all[fc_all["country"] == tc].to_csv(PBI_DIR / "forecasts.csv", index=False)
    (imp_all[imp_all["country"] == tc].drop(columns="country")
        .to_csv(PBI_DIR / "feature_importance.csv", index=False))
    if all_shap:
        s = pd.concat(all_shap, ignore_index=True)
        (s[s["country"] == tc].drop(columns="country")
            .to_csv(PBI_DIR / "shap_importance.csv", index=False))

    print(f"\n  Power BI files use target country: {tc}")
    print(f"  App files cover all {comp_all['country'].nunique()} countries")
    print(f"  Folder: {PBI_DIR.relative_to(config.PROJECT_ROOT)}")


if __name__ == "__main__":
    export()
