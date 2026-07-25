"""
db.py
=====
Everything about connecting to YOUR SQL Server lives here, so no other file has
to know the connection details.

- Uses Windows Authentication (Trusted_Connection) -> logs in as your Windows
  account, no password needed.
- Auto-detects which "ODBC Driver for SQL Server" is installed on your PC.
- Creates the PAM_CO2 database automatically the first time you run.

If you ever move to a different server, you only change SQL_SERVER / SQL_DATABASE
in config.py — nothing here.
"""

from __future__ import annotations

import urllib.parse

import pyodbc
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src import config

# Drivers we know how to use, best first. We pick whichever is installed.
_PREFERRED_DRIVERS = [
    "ODBC Driver 18 for SQL Server",
    "ODBC Driver 17 for SQL Server",
    "SQL Server Native Client 11.0",
    "SQL Server",
]


def _pick_driver() -> str:
    """Return the best SQL Server ODBC driver installed on this machine."""
    installed = [d for d in pyodbc.drivers()]
    for driver in _PREFERRED_DRIVERS:
        if driver in installed:
            return driver
    raise RuntimeError(
        "No SQL Server ODBC driver found. Please install "
        "'ODBC Driver 17 for SQL Server' from Microsoft.\n"
        f"Drivers currently installed: {installed}"
    )


def _odbc_connection_string(database: str) -> str:
    """Build a raw ODBC connection string for the given database."""
    driver = _pick_driver()
    parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={config.SQL_SERVER}",
        f"DATABASE={database}",
        "Trusted_Connection=yes",          # Windows Authentication
    ]
    # ODBC Driver 18 encrypts by default and rejects the self-signed local
    # certificate. For a local instance we turn that off so it connects.
    if "18" in driver:
        parts.append("Encrypt=no")
        parts.append("TrustServerCertificate=yes")
    return ";".join(parts)


def get_engine(database: str | None = None) -> Engine:
    """Return a SQLAlchemy engine connected to the project database.

    fast_executemany=True makes bulk inserts (our 47k rows) fast.
    """
    database = database or config.SQL_DATABASE
    odbc_str = _odbc_connection_string(database)
    params = urllib.parse.quote_plus(odbc_str)
    url = f"mssql+pyodbc:///?odbc_connect={params}"
    return create_engine(url, fast_executemany=True)


def ensure_database() -> None:
    """Create the project database if it does not already exist.

    We connect to the built-in 'master' database first (which always exists),
    then CREATE DATABASE. autocommit=True is required because CREATE DATABASE
    cannot run inside a transaction.
    """
    master_conn = pyodbc.connect(_odbc_connection_string("master"), autocommit=True)
    try:
        cur = master_conn.cursor()
        cur.execute(
            f"IF DB_ID('{config.SQL_DATABASE}') IS NULL "
            f"CREATE DATABASE [{config.SQL_DATABASE}]"
        )
        print(f"  database '{config.SQL_DATABASE}' is ready on {config.SQL_SERVER}")
    finally:
        master_conn.close()


def run_ddl_script(sql_text: str, engine: Engine) -> None:
    """Execute a multi-statement DDL script (schema.sql).

    SQLAlchemy runs one statement at a time, so we split the script on ';'.
    Our schema has no semicolons inside statements, so this is safe.
    """
    with engine.begin() as conn:
        for statement in sql_text.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
