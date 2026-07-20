# 🌍 CO₂ Emission Forecasting for Climate Policy

> Benchmarking statistical and machine learning models on daily CO₂ emissions —
> replicating a 2025 peer-reviewed study and assessing which models best support
> evidence-based climate policy.

<!-- Badges: these become live once CI and the demo exist (Week 6).
[![CI](https://github.com/dharmikdave29/co2-emission-forecasting/actions/workflows/ci.yml/badge.svg)](../../actions)
[![Live Demo](https://img.shields.io/badge/demo-streamlit-red)](YOUR_APP_URL)
-->
![Python](https://img.shields.io/badge/python-3.11+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-week%201%20of%207-orange)

---

## 📌 Overview

Accurate short-term CO₂ forecasts help governments set emission targets and
evaluate interventions. This project asks: **which forecasting approach should a
policy analyst actually use?**

It replicates and extends *Ajala et al. (2025)* — a comparison of statistical,
machine learning, and deep learning models for daily CO₂ prediction — using
publicly available [Carbon Monitor](https://carbonmonitor.org) data for
**China, India, USA, and EU27+UK**.

### Research questions

| # | Question |
|---|----------|
| RQ1 | Can published forecasting results be replicated using publicly available datasets? |
| RQ2 | Which forecasting approach is most suitable for policy analysis and decision support? |
| RQ3 | What trade-offs exist between accuracy, interpretability, and computational complexity? |

---

## 🏗️ Architecture

```
Carbon Monitor / OWID  ──▶  Python ETL  ──▶  SQL database (PostgreSQL/SQLite)
                                                   │
                              ┌────────────────────┼──────────────────┐
                              ▼                    ▼                  ▼
                        ARIMA baseline      RF / GB / XGBoost    Power BI dashboard
                        (statsmodels)       (scikit-learn)       (policy view)
                              │                    │
                              └────────┬───────────┘
                                       ▼
                         Evaluation: R² · RMSE · MAE · MAPE
                                       ▼
                            Streamlit forecast explorer
```

---

## 📊 Data

| Source | Granularity | Used for |
|--------|------------|----------|
| [Carbon Monitor](https://carbonmonitor.org) | Daily, by country & sector, 2019– | Primary modeling dataset |
| [Our World in Data](https://github.com/owid/co2-data) | Annual, by country | Context & socioeconomic features |

Data is **not stored in this repo** — run `src/data/download.py` to fetch it
(reproducibility over bundled CSVs).

---

## 🤖 Models

| Model | Type | Why it's here |
|-------|------|---------------|
| ARIMA / SARIMA | Statistical | Interpretable baseline; the policy-world standard |
| Random Forest | ML (bagging) | Non-linear patterns, built-in feature importance |
| Gradient Boosting | ML (boosting) | Top published accuracy (R² > 0.93 in Ajala et al.) |
| XGBoost | ML (boosting) | Modern industry-standard variant |

Evaluation uses a **chronological 80/20 split** and `TimeSeriesSplit`
cross-validation — never random splits, which would leak future data.

---

## 📈 Results

> 🚧 Coming in Week 5. Target benchmarks from the literature:
> ARIMA R² ≈ 0.72 · Random Forest R² ≈ 0.92 · Gradient Boosting R² > 0.93

| Model | R² | RMSE | MAE | MAPE |
|-------|----|------|-----|------|
| ARIMA | – | – | – | – |
| Random Forest | – | – | – | – |
| Gradient Boosting | – | – | – | – |
| XGBoost | – | – | – | – |

---

## 📁 Repository structure

```
├── data/            # raw & processed data (gitignored, created by scripts)
├── sql/             # schema + analytical queries
├── notebooks/       # EDA and model exploration
├── src/
│   ├── data/        # download.py, etl.py
│   ├── features/    # lag & calendar feature engineering
│   ├── models/      # arima_model.py, ml_models.py, evaluate.py
│   └── visualization/
├── app/             # Streamlit app
├── powerbi/         # dashboard + screenshots
├── reports/figures/ # generated plots
└── tests/           # pytest unit tests
```

---

## 🚀 Setup

```bash
git clone https://github.com/dharmik-29/co2-emission-forecasting.git
cd co2-emission-forecasting
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
python src/data/download.py   # fetch datasets
```

---

## 🗺️ Roadmap

- [x] **Week 1** — Repo setup, data acquisition, EDA
- [ ] **Week 2** — SQL schema, ETL pipeline, analytical queries
- [ ] **Week 3** — ARIMA baseline with diagnostics
- [ ] **Week 4** — RF, Gradient Boosting, XGBoost + TimeSeriesSplit CV
- [ ] **Week 5** — Model comparison, SHAP, Power BI dashboard
- [ ] **Week 6** — Streamlit app, CI, Docker
- [ ] **Week 7** — Polish, write-up, live demo

---

## 📚 Key references

- Ajala, M. A., et al. (2025). *Daily CO₂ emissions prediction: ML, DL & statistical models.* Science and Technology for Energy Transition.
- Li, X. (2023). *Comparative study of statistical and ML models on near-real-time daily CO₂ prediction.* arXiv:2302.01152.
- Ulussever, T., et al. (2023). *ML vs time-series econometric models for sector-based CO₂ in the USA.* Environ. Sci. Pollut. Res.
- Giannelos, S., et al. (2024). *ML approaches for CO₂ predictions in the building sector.* Electric Power Systems Research.

---

## 👤 Author

**Dharmik Dave** — MSc E-Government, University of Koblenz
[Portfolio](https://your-site.com) · [LinkedIn](https://linkedin.com/in/your-profile) · [GitHub](https://github.com/dharmikdave29)

Licensed under the [MIT License](LICENSE).
