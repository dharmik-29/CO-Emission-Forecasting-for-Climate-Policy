"""
main.py
=======
Run the ENTIRE pipeline end-to-end with one command:

    python main.py

Steps:
  1. Download data          (src/data/download.py)
  2. ETL into SQLite        (src/data/etl.py)
  3. Analytical SQL queries (src/data/queries.py)
  4. Feature engineering    (src/features/build_features.py)
  5. ARIMA baseline         (src/models/arima_model.py)
  6. ML models              (src/models/ml_models.py)
  7. Results + figures      (src/visualization/plots.py)
"""

from __future__ import annotations

import pandas as pd

from src import config
from src.data.download import download
from src.data.etl import run_etl
from src.data.queries import run_all
from src.features.build_features import build_features, load_series_from_db
from src.models.arima_model import adf_test, fit_and_forecast
from src.models.ml_models import train_and_evaluate
from src.visualization import plots


def main() -> None:
    print("=" * 64)
    print(f"CO2 EMISSION FORECASTING PIPELINE  ·  target: {config.TARGET_COUNTRY}")
    print(f"SQL Server: {config.SQL_SERVER}  ·  database: {config.SQL_DATABASE}")
    print("=" * 64)

    # 1-2. Data + ETL
    download()
    run_etl()

    # 3. SQL analytics
    sql_results = run_all()
    print("\n  Country ranking by total emissions (from SQL):")
    print(sql_results["country_totals"].to_string(index=False))

    # 4. Features — for the target country only
    print(f"\nSTEP 4 · Feature engineering (target: {config.TARGET_COUNTRY})")
    series = load_series_from_db()
    feats = build_features(series)
    print(f"  {feats.shape[0]} rows x {feats.shape[1] - 1} predictors")

    # Chronological 80/20 split (never random for time series)
    split_idx = int(len(series) * config.TRAIN_FRACTION)
    split_date = series.index[split_idx]
    train_s, test_s = series.iloc[:split_idx], series.iloc[split_idx:]
    print(f"  train: {train_s.index[0].date()} .. {train_s.index[-1].date()} "
          f"({len(train_s)} days)")
    print(f"  test : {test_s.index[0].date()} .. {test_s.index[-1].date()} "
          f"({len(test_s)} days)")

    # 5. ARIMA
    print("\nSTEP 5 · ARIMA baseline")
    adf_test(series)
    arima_pred, _order, arima_result = fit_and_forecast(train_s, test_s)

    # 6. ML models
    print("\nSTEP 6 · Machine learning models")
    ml_results, extras, ml_preds = train_and_evaluate(feats, split_date)

    # 7. Results table + figures
    print("\nSTEP 7 · Results")
    table = (pd.DataFrame([arima_result] + ml_results)
             .set_index("model").round(3))
    print(table.to_string())
    best = table["R2"].idxmax()
    print(f"\n  Best model: {best}")

    table.to_csv(config.REPORTS_DIR / "model_comparison.csv")
    print(f"  saved metrics -> reports/model_comparison.csv")

    plots.plot_series(series)
    plots.plot_forecasts(extras["y_test"], arima_pred, ml_preds)
    plots.plot_importance(extras["importance"])

    print("\n" + "=" * 64)
    print("PIPELINE COMPLETE")
    print("=" * 64)


if __name__ == "__main__":
    main()
