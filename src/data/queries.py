"""
queries.py
==========
Step 3 of the pipeline: run the analytical T-SQL in sql/analysis_queries.sql
against SQL Server and return the results as pandas DataFrames.

The .sql file is the single source of truth for the SQL — this module just
parses out the named blocks (marked with '-- name: X') and executes them.
That keeps the SQL in a real .sql file you can also open directly in SSMS.

Run directly:
    python -m src.data.queries
"""

from __future__ import annotations

import re

import pandas as pd

from src import config
from src.data.db import get_engine


def _parse_named_queries() -> dict[str, str]:
    """Split analysis_queries.sql into {name: sql} using the '-- name: X' tags.

    We also swap the literal 'China' in the .sql file for config.TARGET_COUNTRY
    so, if you change the target country in config.py, the SQL follows along.
    """
    text = (config.SQL_DIR / "analysis_queries.sql").read_text(encoding="utf-8")

    # Keep the SQL and the modelling target in sync.
    if config.TARGET_COUNTRY != "China":
        text = text.replace("'China'", f"'{config.TARGET_COUNTRY}'")

    # Match a '-- name: X' tag only at the START of a line (re.MULTILINE),
    # so mentions of the tag inside comments are not treated as real tags.
    blocks = re.split(r"(?m)^--\s*name:\s*(\w+)\s*$", text)
    # re.split keeps the captured names: [preamble, name1, body1, name2, body2, ...]
    queries: dict[str, str] = {}
    for i in range(1, len(blocks), 2):
        name = blocks[i].strip()
        body = blocks[i + 1]
        # Drop trailing comment-only lines so each block is a single statement
        queries[name] = _clean_sql(body)
    return queries
def _clean_sql(body: str) -> str:
    """Return one runnable statement: drop comment-only lines and trailing ';'."""
    lines = [ln for ln in body.splitlines()
             if ln.strip() and not ln.strip().startswith("--")]
    return "\n".join(lines).strip().rstrip(";").strip()


def run_all() -> dict[str, pd.DataFrame]:
    """Execute every named query and return a dict of DataFrames."""
    print("STEP 3 · Running analytical SQL queries")
    from src.data.db import get_engine
    engine = get_engine()

    queries = _parse_named_queries()
    results: dict[str, pd.DataFrame] = {}

    raw = engine.raw_connection()             # underlying pyodbc connection
    try:
        cursor = raw.cursor()
        for name, sql in queries.items():
            cursor.execute(sql)
            # SQL Server can return an empty result set first — skip to the
            # one that actually has columns.
            while cursor.description is None and cursor.nextset():
                pass
            columns = [col[0] for col in cursor.description]
            rows = [tuple(r) for r in cursor.fetchall()]
            results[name] = pd.DataFrame(rows, columns=columns)
            print(f"  {name:<18} -> {len(results[name]):>4} rows")
        cursor.close()
    finally:
        raw.close()
    return results


if __name__ == "__main__":
    out = run_all()
    print("\nCountry ranking (total emissions):")
    print(out["country_totals"].to_string(index=False))
