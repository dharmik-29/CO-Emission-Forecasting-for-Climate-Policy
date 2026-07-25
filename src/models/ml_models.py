"""
ml_models.py
============
Step 5b: the machine-learning models (Random Forest & Gradient Boosting).

These learn non-linear patterns from the engineered features. They are trained
and tested on the SAME chronological split as ARIMA so the comparison is fair.
XGBoost is added if the optional package is installed.
"""

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor

from src import config
from src.models.evaluate import metrics


def get_models() -> dict:
    """Return the ML models to train. XGBoost is optional (added if installed)."""
    models = {
        "RandomForest": RandomForestRegressor(
            n_estimators=100, max_depth=10,
            random_state=config.RANDOM_STATE, n_jobs=-1),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=200, learning_rate=0.1, max_depth=3,
            random_state=config.RANDOM_STATE),
    }
    try:
        from xgboost import XGBRegressor
        models["XGBoost"] = XGBRegressor(
            n_estimators=300, learning_rate=0.05, max_depth=4,
            random_state=config.RANDOM_STATE, verbosity=0)
    except ImportError:
        print("  (xgboost not installed - skipping; pip install xgboost to enable)")
    return models


def train_and_evaluate(feats: pd.DataFrame, split_date) -> tuple[list, dict, pd.Series]:
    """Train every ML model on the chronological split and return metrics + predictions."""
    X, y = feats.drop(columns="y"), feats["y"]
    X_train, X_test = X.loc[:split_date], X.loc[split_date:].iloc[1:]
    y_train, y_test = y.loc[X_train.index], y.loc[X_test.index]

    results, predictions = [], {}
    for name, model in get_models().items():
        model.fit(X_train, y_train)
        pred = pd.Series(model.predict(X_test), index=y_test.index)
        predictions[name] = pred
        results.append(metrics(y_test.values, pred.values, name))
        print(f"  trained {name}")

    # Feature importance from the Random Forest (policy interpretability, RQ2)
    rf = get_models()["RandomForest"].fit(X_train, y_train)
    importance = (pd.Series(rf.feature_importances_, index=X.columns)
                  .sort_values(ascending=False))
    return results, {"importance": importance, "y_test": y_test}, predictions
