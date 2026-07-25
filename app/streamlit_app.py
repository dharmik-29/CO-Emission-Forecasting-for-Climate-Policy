"""
streamlit_app.py
================
Week 6 deliverable: an interactive forecast-explorer web app.

It reads the CSVs exported by src/reporting/powerbi_export.py, so it runs
anywhere (no SQL Server needed) — perfect for a free public deployment on
Streamlit Community Cloud.

Run locally:
    streamlit run app/streamlit_app.py

Deploy free:
    Push to GitHub -> https://share.streamlit.io -> point it at this file.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

# ── Locate the exported data (powerbi/ folder next to the project root) ────
APP_DIR = Path(__file__).resolve().parent
PBI_DIR = APP_DIR.parent / "powerbi"

st.set_page_config(page_title="CO₂ Emission Forecasting", page_icon="🌍",
                   layout="wide")


@st.cache_data
def load_csv(name: str) -> pd.DataFrame:
    """Load a CSV from the powerbi/ folder, parsing dates where present."""
    path = PBI_DIR / name
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


daily = load_csv("daily_emissions.csv")
comparison = load_csv("model_comparison.csv")
forecasts = load_csv("forecasts.csv")
shap_imp = load_csv("shap_importance.csv")

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🌍 CO₂ Emission Forecasting for Climate Policy")
st.caption("Benchmarking ARIMA vs Random Forest vs Gradient Boosting on daily "
           "Carbon Monitor data · Dharmik Dave")

if daily.empty:
    st.error("No data found. Run `python -m src.reporting.powerbi_export` first "
             "to generate the CSVs in the powerbi/ folder.")
    st.stop()

# ── Sidebar controls ───────────────────────────────────────────────────────
st.sidebar.header("Filters")
countries = sorted(daily["country"].unique())
default_ix = countries.index("China") if "China" in countries else 0
country = st.sidebar.selectbox("Country / region", countries, index=default_ix)

sectors = sorted(daily["sector"].unique())
chosen_sectors = st.sidebar.multiselect("Sectors", sectors, default=sectors)

# ── KPI row ────────────────────────────────────────────────────────────────
mask = (daily["country"] == country) & (daily["sector"].isin(chosen_sectors))
sub = daily[mask]

col1, col2, col3 = st.columns(3)
col1.metric("Total CO₂ (Mt)", f"{sub['mtco2_per_day'].sum():,.0f}")
col2.metric("Avg daily CO₂ (Mt)",
            f"{sub.groupby('date')['mtco2_per_day'].sum().mean():,.2f}")
if not comparison.empty:
    best = comparison.loc[comparison["R2"].idxmax()]
    col3.metric("Best model (R²)", f"{best['model']}  ({best['R2']:.3f})")

# ── Emissions over time ────────────────────────────────────────────────────
st.subheader(f"Daily emissions over time — {country}")
ts = sub.groupby("date")["mtco2_per_day"].sum()
st.line_chart(ts, height=280)

# ── Model comparison + forecast ────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader("Model accuracy")
    if not comparison.empty:
        st.dataframe(comparison.set_index("model").round(3),
                     use_container_width=True)
        st.bar_chart(comparison.set_index("model")["R2"], height=240)

with right:
    st.subheader("Forecast vs actual (hold-out)")
    if not forecasts.empty:
        fc = forecasts
        if "country" in fc.columns:
            fc = fc[fc["country"] == country]
        if not fc.empty:
            cols = [c for c in ["actual", "ARIMA", "RandomForest",
                                "GradientBoosting"] if c in fc.columns]
            st.line_chart(fc.set_index("date")[cols], height=240)
        else:
            st.info(f"Forecasts were generated for a different country. "
                    f"Re-run the export with TARGET_COUNTRY = '{country}'.")

# ── Interpretability ───────────────────────────────────────────────────────
if not shap_imp.empty:
    st.subheader("What drives the forecast? (SHAP interpretability)")
    st.bar_chart(shap_imp.set_index("feature")["mean_abs_shap"], height=240)
    st.caption("Higher = the feature has more influence on the model's "
               "predictions. Recent history (lag_1, 7-day average) dominates.")

st.divider()
st.caption("Data: carbonmonitor.org · Models: statsmodels + scikit-learn · "
           "Built for the PAM CO₂ project.")
