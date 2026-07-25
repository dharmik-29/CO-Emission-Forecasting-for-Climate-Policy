-- analysis_queries_sqlserver.sql
-- ==============================
-- SQL SERVER (T-SQL) version of the analytical queries.
--
-- Use this file ONLY if you are running in SQL Server Management Studio (SSMS)
-- or Azure Data Studio. The main sql/analysis_queries.sql is SQLite dialect
-- (that's what the Python pipeline uses). This file swaps the SQLite-only
-- functions for their T-SQL equivalents:
--     strftime('%Y-%m', date) -> LEFT(date, 7)        (date is stored as text yyyy-mm-dd)
--     strftime('%Y', date)    -> LEFT(date, 4)
--     strftime('%w', date)    -> DATENAME/DATEPART(WEEKDAY, ...)
--     LIMIT n                 -> SELECT TOP n
--     derived table           -> must have an alias (AS t)
--
-- PREREQUISITE: the daily_emissions table must exist in your SQL Server
-- database. See sql/schema_sqlserver.sql to create it, then load the CSV
-- (data/raw/carbon_monitor_daily.csv) via SSMS "Import Flat File" wizard.


-- ── country_totals ───────────────────────────────────────────────────────
-- Which countries emit the most over the whole period? (ranking)
SELECT country,
       ROUND(SUM(mtco2_per_day), 1) AS total_mtco2,
       ROUND(AVG(mtco2_per_day), 3) AS avg_sector_day
FROM daily_emissions
GROUP BY country
ORDER BY total_mtco2 DESC;


-- ── sector_breakdown ─────────────────────────────────────────────────────
-- Within one country, which sectors drive emissions?
-- SUM() OVER () gives the country total so we can compute a % share.
SELECT sector,
       ROUND(SUM(mtco2_per_day), 1)                               AS total_mtco2,
       ROUND(100.0 * SUM(mtco2_per_day)
             / SUM(SUM(mtco2_per_day)) OVER (), 1)                AS pct_of_country
FROM daily_emissions
WHERE country = 'China'
GROUP BY sector
ORDER BY total_mtco2 DESC;


-- ── monthly_trend ────────────────────────────────────────────────────────
-- How do one country's total emissions evolve month by month?
-- LEFT(date, 7) turns 'yyyy-mm-dd' text into 'yyyy-mm'.
SELECT LEFT(date, 7)                AS month,
       ROUND(SUM(mtco2_per_day), 1) AS total_mtco2
FROM daily_emissions
WHERE country = 'China'
GROUP BY LEFT(date, 7)
ORDER BY month;


-- ── rolling_30d_avg ──────────────────────────────────────────────────────
-- Underlying trend once daily noise is smoothed (WINDOW FUNCTION).
-- NOTE: the derived table MUST have an alias ('AS daily') in SQL Server.
SELECT date,
       ROUND(daily_total, 2) AS daily_mtco2,
       ROUND(AVG(daily_total) OVER (
           ORDER BY date
           ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
       ), 2) AS rolling_30d_avg
FROM (
    SELECT date, SUM(mtco2_per_day) AS daily_total
    FROM daily_emissions
    WHERE country = 'China'
    GROUP BY date
) AS daily
ORDER BY date;


-- ── yearly_change ────────────────────────────────────────────────────────
-- Is the country's output growing or shrinking each year? (CTE + self-join)
WITH yearly AS (
    SELECT LEFT(date, 4)              AS year,
           ROUND(SUM(mtco2_per_day), 0) AS total_mtco2
    FROM daily_emissions
    WHERE country = 'China'
    GROUP BY LEFT(date, 4)
)
SELECT y.year,
       y.total_mtco2,
       ROUND(100.0 * (y.total_mtco2 - p.total_mtco2) / p.total_mtco2, 2)
           AS yoy_change_pct
FROM yearly y
LEFT JOIN yearly p
       ON CAST(p.year AS INT) = CAST(y.year AS INT) - 1
ORDER BY y.year;


-- ── weekday_pattern ──────────────────────────────────────────────────────
-- How much lower are weekend emissions? (transport policy)
-- DATENAME gives the day name; DATEPART(WEEKDAY) orders Mon..Sun correctly.
SELECT DATENAME(WEEKDAY, CAST(date AS date))          AS weekday,
       ROUND(SUM(mtco2_per_day)
             / COUNT(DISTINCT date), 2)               AS avg_daily_mtco2
FROM daily_emissions
WHERE country = 'China'
GROUP BY DATENAME(WEEKDAY, CAST(date AS date)),
         DATEPART(WEEKDAY, CAST(date AS date))
ORDER BY DATEPART(WEEKDAY, CAST(date AS date));


-- ── top_emission_days ────────────────────────────────────────────────────
-- Which specific days had the highest total emissions? (TOP instead of LIMIT)
SELECT TOP 5
       date,
       ROUND(SUM(mtco2_per_day), 2) AS daily_total
FROM daily_emissions
WHERE country = 'China'
GROUP BY date
ORDER BY daily_total DESC;
