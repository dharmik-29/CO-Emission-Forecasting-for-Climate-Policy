"""
etl.py
======
Step 2 of the pipeline: Extract-Transform-Load into SQL Server.

- EXTRACT   : read the clean CSV produced by download.py
- TRANSFORM : final safety checks (types, duplicates, sort)
- LOAD      : create the table (schema.sql) and bulk-insert into SQL Server

The connection is handled entirely by src/data/db.py, which is pre-configured
for your server (localhost\SQLEXPRESS01, database PAM_CO2, Windows auth).

Run directly:
    python -m src.data.etl
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from src import config
from src.data.db import ensure_database, get_engine, run_ddl_script


def extract() -> pd.DataFrame:
    """Read the clean CSV into a DataFrame."""
    df = pd.read_csv(config.RAW_CSV, parse_dates=["date"])
    print(f"  extracted {len(df):,} rows from {config.RAW_CSV.name}")
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Final cleaning: standardise columns, drop duplicates, ensure numeric, sort."""
    df = df.copy()  # work on our own copy so pandas never warns about views
    df.columns = [c.strip().lower() for c in df.columns]

    # Drop exact duplicate measurements (same date + country + sector)
    before = len(df)
    df = df.drop_duplicates(subset=["date", "country", "sector"])
    if before != len(df):
        print(f"  removed {before - len(df)} duplicate row(s)")

    # Guarantee the value column is numeric; drop anything unparseable
    df["mtco2_per_day"] = pd.to_numeric(df["mtco2_per_day"], errors="coerce")
    df = df.dropna(subset=["mtco2_per_day"])

    # Sort chronologically within each country — essential for time-series work
    df = df.sort_values(["country", "date", "sector"]).reset_index(drop=True)
    print(f"  transformed -> {len(df):,} clean rows")
    return df


def load(df: pd.DataFrame) -> None:
    """Create the schema and bulk-load the cleaned data into SQL Server."""
    ensure_database()                 # create PAM_CO2 if it does not exist
    engine = get_engine()

    # Create the table (DROP + CREATE + INDEXES) from the T-SQL schema file
    schema_sql = (config.SQL_DIR / "schema.sql").read_text(encoding="utf-8")
    run_ddl_script(schema_sql, engine)

    # Store dates as text 'yyyy-mm-dd' to match the VARCHAR(10) column
    out = df.copy()
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")

    # Bulk insert. chunksize keeps memory low; fast_executemany makes it quick.
    out[["date", "country", "sector", "mtco2_per_day"]].to_sql(
        "daily_emissions", engine, if_exists="append", index=False, chunksize=1000
    )

    # Confirm what landed in the database
    with engine.connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM daily_emissions")).scalar()
        c = conn.execute(
            text("SELECT COUNT(DISTINCT country) FROM daily_emissions")).scalar()
    print(f"  loaded {n:,} rows ({c} countries) into "
          f"{config.SQL_DATABASE}.dbo.daily_emissions")


def run_etl() -> pd.DataFrame:
    """Full ETL: extract -> transform -> load. Returns the clean DataFrame."""
    print("STEP 2 · ETL into SQL Server")
    df = transform(extract())
    load(df)
    return df


if __name__ == "__main__":
    run_etl()
