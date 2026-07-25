"""
streamlit_app.py
================
Interactive forecast-explorer web app for daily CO2 emissions.

Reads the CSVs exported by src/reporting/powerbi_export.py, so it runs anywhere
(no SQL Server needed) — ideal for a free deployment on Streamlit Community Cloud.

The '..._all.csv' files carry a 'country' column, so every country the user
picks shows its own forecast, model scores and SHAP drivers.

Run locally:   streamlit run app/streamlit_app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
PBI_DIR = APP_DIR.parent / "powerbi"

st.set_page_config(page_title="CO2 Emission Forecasting", page_icon="🌍",
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
# Prefer the all-country files; fall back to the single-country ones.
comparison = load_csv("model_comparison_all.csv")
if comparison.empty:
    comparison = load_csv("model_comparison.csv")
forecasts = load_csv("forecasts_all.csv")
if forecasts.empty:
    forecasts = load_csv("forecasts.csv")
shap_imp = load_csv("shap_all.csv")
if shap_imp.empty:
    shap_imp = load_csv("shap_importance.csv")

# ── Header ─────────────────────────────────────────────────────────────────
st.title("🌍 CO2 Emission Forecasting for Climate Policy")
st.caption("Benchmarking ARIMA vs Random Forest vs Gradient Boosting on daily "
           "Carbon Monitor data · Dharmik Dave")

if daily.empty:
    st.error("No data found. Run `python -m src.reporting.powerbi_export` first.")
    st.stop()


def by_country(df: pd.DataFrame, country: str) -> pd.DataFrame:
    """Filter a dataframe to one country if it has a 'country' column."""
    if not df.empty and "country" in df.columns:
        return df[df["country"] == country]
    return df

# ── Sidebar controls ───────────────────────────────────────────────────────
st.sidebar.header("Filters")
countries = sorted(daily["country"].unique())
default_ix = countries.index("China") if "China" in countries else 0
country = st.sidebar.selectbox("Country / region", countries, index=default_ix)

sectors = sorted(daily["sector"].unique())
chosen_sectors = st.sidebar.multiselect("Sectors", sectors, default=sectors)

# Slices for the selected country
sub = daily[(daily["country"] == country) & (daily["sector"].isin(chosen_sectors))]
comp_c = by_country(comparison, country)
fc_c = by_country(forecasts, country)
shap_c = by_country(shap_imp, country)

# ── KPI row ────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("Total CO2 (Mt)", f"{sub['mtco2_per_day'].sum():,.0f}")
col2.metric("Avg daily CO2 (Mt)",
            f"{sub.groupby('date')['mtco2_per_day'].sum().mean():,.2f}")
if not comp_c.empty:
    best = comp_c.loc[comp_c["R2"].idxmax()]
    col3.metric("Best model (R²)", f"{best['model']}  ({best['R2']:.3f})")

# ── Emissions over time ────────────────────────────────────────────────────
st.subheader(f"Daily emissions over time — {country}")
st.line_chart(sub.groupby("date")["mtco2_per_day"].sum(), height=280)

# ── Model comparison + forecast ────────────────────────────────────────────
left, right = st.columns(2)

with left:
    st.subheader(f"Model accuracy — {country}")
    if not comp_c.empty:
        table = comp_c.drop(columns=[c for c in ["country"] if c in comp_c.columns])
        st.dataframe(table.set_index("model").round(3), use_container_width=True)
        st.bar_chart(comp_c.set_index("model")["R2"], height=240)

with right:
    st.subheader("Forecast vs actual (hold-out)")
    if not fc_c.empty:
        cols = [c for c in ["actual", "ARIMA", "RandomForest", "GradientBoosting"]
                if c in fc_c.columns]
        st.line_chart(fc_c.set_index("date")[cols], height=240)
    else:
        st.info("No forecast available for this country yet.")

# ── Interpretability ───────────────────────────────────────────────────────
if not shap_c.empty:
    st.subheader(f"What drives the forecast? — {country} (SHAP)")
    ranked = shap_c.sort_values("mean_abs_shap", ascending=False)
    st.bar_chart(ranked.set_index("feature")["mean_abs_shap"], height=240)
    st.caption("Higher = more influence on the model's predictions. "
               "Recent history (lag_1, 7-day average) dominates.")

st.divider()
st.caption("Data: carbonmonitor.org · Models: statsmodels + scikit-learn · "
           "PAM CO2 project.")
