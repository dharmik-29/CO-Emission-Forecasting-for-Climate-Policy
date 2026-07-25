"""
config.py
=========
Central place for all project paths and settings. Every other module imports
from here so there are no hard-coded values scattered around the codebase.
"""

from pathlib import Path

# ── Directories ──────────────────────────────────────────────────────────
# PROJECT_ROOT is two levels up from this file (src/config.py -> src -> root).
# It is computed dynamically, so the project works no matter where you put the
# folder on disk (e.g. C:\Dharmik\projects\PAM CO2 project).
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"
SQL_DIR = PROJECT_ROOT / "sql"

# Make sure the folders exist when the project runs
for _d in (RAW_DIR, PROCESSED_DIR, FIGURES_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ── Files ────────────────────────────────────────────────────────────────
# The raw Carbon Monitor Excel you downloaded from carbonmonitor.org.
# It is bundled in data/raw/ so the project runs out of the box.
RAW_XLSX = RAW_DIR / "carbon-monitor-GLOBAL-maingraphdatas.xlsx"
RAW_CSV = RAW_DIR / "carbon_monitor_daily.csv"   # cleaned CSV produced by download.py

# ── SQL Server connection ────────────────────────────────────────────────
# These match YOUR machine. Windows Authentication is used (Trusted_Connection),
# so no username/password is needed — it logs in as your Windows account.
#   Server instance : localhost\SQLEXPRESS01
#   Database        : PAM_CO2  (created automatically on first run)
SQL_SERVER = r"localhost\SQLEXPRESS01"
SQL_DATABASE = "PAM_CO2"

# ── Data scope ───────────────────────────────────────────────────────────
# The countries/regions present in the Carbon Monitor global file.
SELECTED_COUNTRIES = [
    "China", "United States", "India", "EU27", "Russian Federation",
    "Japan", "Brazil", "United Kingdom", "ROW",
]

# ── Modelling constants ──────────────────────────────────────────────────
# Which country/region to forecast. China is the largest emitter and the main
# focus of Ajala et al. (2025). Change this to model a different country.
TARGET_COUNTRY = "China"

TRAIN_FRACTION = 0.80         # chronological train/test split (first 80% train)
LAGS = (1, 7, 30)             # lag features (yesterday, last week, last month)
RANDOM_STATE = 42             # fixed seed so results are reproducible
