"""
download.py
===========
Step 1 of the pipeline: turn the raw Carbon Monitor Excel file into a clean CSV.

The real data comes from https://carbonmonitor.org (the "GLOBAL main graph data"
Excel export). You download that file once by hand and drop it into data/raw/.
This script then:
  1. reads the Excel sheet
  2. strips the 3 footer/junk rows Carbon Monitor adds at the bottom
     (they contain 'carbonmonitor.org' and the export date, not real data)
  3. keeps only our selected countries
  4. writes a tidy CSV: date, country, sector, mtco2_per_day

If the Excel file is missing, it falls back to a small SYNTHETIC dataset so the
pipeline still runs (useful for a quick demo or CI).

Run directly:
    python -m src.data.download
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src import config

# The exact column names inside the Carbon Monitor Excel file.
EXCEL_COLUMNS = {
    "country": "country",
    "date": "date",
    "sector": "sector",
    "MtCO2 per day": "mtco2_per_day",   # rename to a clean snake_case name
}


def _make_synthetic(n_days: int = 881, seed: int = 42) -> pd.DataFrame:
    """Fallback only: realistic daily CO2 for one country, all 6 sectors."""
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2024-01-01", periods=n_days, freq="D")
    sectors = ["Power", "Industry", "Ground Transport",
               "Residential", "Domestic Aviation", "International Aviation"]
    rows = []
    t = np.arange(n_days)
    for sec, base in zip(sectors, [12, 8, 6, 3, 0.3, 0.2]):
        vals = (base
                + 0.4 * np.sin(2 * np.pi * t / 7)          # weekly rhythm
                + base * 0.15 * np.sin(2 * np.pi * t / 365) # annual season
                + rng.normal(0, base * 0.05, n_days))       # noise
        for d, v in zip(dates, vals):
            rows.append((d, "China", sec, max(v, 0)))
    return pd.DataFrame(rows, columns=["date", "country", "sector", "mtco2_per_day"])


def _load_excel() -> pd.DataFrame | None:
    """Read and clean the Carbon Monitor Excel. Returns None if the file is absent."""
    if not config.RAW_XLSX.exists():
        print(f"  Excel not found at {config.RAW_XLSX.relative_to(config.PROJECT_ROOT)}")
        return None

    # engine='openpyxl' is required to read .xlsx files
    df = pd.read_excel(config.RAW_XLSX, sheet_name="datas", engine="openpyxl")
    df = df.rename(columns=EXCEL_COLUMNS)

    # Parse dates. dayfirst=True because Carbon Monitor uses dd/mm/yyyy.
    # The 3 footer rows have non-date text here, so they become NaT and are dropped.
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")

    # The value column must be numeric; footer rows become NaN and are dropped.
    df["mtco2_per_day"] = pd.to_numeric(df["mtco2_per_day"], errors="coerce")

    before = len(df)
    df = df.dropna(subset=["date", "country", "sector", "mtco2_per_day"])
    print(f"  dropped {before - len(df)} junk/footer row(s)")

    # Keep only the countries we chose to study.
    df = df[df["country"].isin(config.SELECTED_COUNTRIES)]

    return df[["date", "country", "sector", "mtco2_per_day"]]


def download() -> pd.DataFrame:
    """Main entry point: produce data/raw/carbon_monitor_daily.csv."""
    print("STEP 1 · Preparing data")
    df = _load_excel()
    if df is None:
        print("  falling back to synthetic data")
        df = _make_synthetic()

    df = df.sort_values(["country", "date", "sector"]).reset_index(drop=True)
    df.to_csv(config.RAW_CSV, index=False)

    n_countries = df["country"].nunique()
    n_days = df["date"].nunique()
    print(f"  wrote {len(df):,} rows "
          f"({n_countries} countries x {n_days} days x sectors) "
          f"-> {config.RAW_CSV.relative_to(config.PROJECT_ROOT)}")
    return df


if __name__ == "__main__":
    download()
