-- comparison_queries.sql  (T-SQL for SQL Server)
-- ===============================================
-- ALL-COUNTRY comparison queries — the bird's-eye view across all 9 countries,
-- to complement analysis_queries.sql (which focuses on one target country).
--
-- Run these in SSMS against the PAM_CO2 database, table dbo.daily_emissions.
-- Each query is independent — highlight one and press Execute, or run them all.


-- ============================================================
-- 1. Country ranking with global share and rank
-- ------------------------------------------------------------
-- Every country's total emissions, its % of the world total, and its rank.
-- Uses two window functions:
--   SUM(...) OVER ()      = grand total across ALL countries (for the % share)
--   RANK() OVER (ORDER..) = position in the league table (1 = biggest emitter)
-- ============================================================
SELECT country,
       ROUND(SUM(mtco2_per_day), 1)                                   AS total_mtco2,
       ROUND(100.0 * SUM(mtco2_per_day)
             / SUM(SUM(mtco2_per_day)) OVER (), 1)                    AS pct_of_world,
       RANK() OVER (ORDER BY SUM(mtco2_per_day) DESC)                 AS rank_position
FROM daily_emissions
GROUP BY country
ORDER BY total_mtco2 DESC;


-- ============================================================
-- 2. Yearly totals — one row per country, one COLUMN per year
-- ------------------------------------------------------------
-- This is the classic "side-by-side" table. We use conditional aggregation:
--   SUM(CASE WHEN year = '2024' THEN value ELSE 0 END)
-- puts each year into its own column so you can compare countries across years
-- at a glance. (LEFT(date, 4) pulls the year out of the 'yyyy-mm-dd' text.)
-- ============================================================
SELECT country,
       ROUND(SUM(CASE WHEN LEFT(date, 4) = '2024' THEN mtco2_per_day ELSE 0 END), 1) AS yr_2024,
       ROUND(SUM(CASE WHEN LEFT(date, 4) = '2025' THEN mtco2_per_day ELSE 0 END), 1) AS yr_2025,
       ROUND(SUM(CASE WHEN LEFT(date, 4) = '2026' THEN mtco2_per_day ELSE 0 END), 1) AS yr_2026
FROM daily_emissions
GROUP BY country
ORDER BY yr_2024 DESC;


-- ============================================================
-- 3. Country x Sector matrix — sectors as columns, countries as rows
-- ------------------------------------------------------------
-- Same conditional-aggregation trick, but splitting by sector instead of year.
-- Lets you see, for example, which countries are Power-heavy vs Transport-heavy.
-- ============================================================
SELECT country,
       ROUND(SUM(CASE WHEN sector = 'Power'            THEN mtco2_per_day ELSE 0 END), 1) AS power,
       ROUND(SUM(CASE WHEN sector = 'Industry'         THEN mtco2_per_day ELSE 0 END), 1) AS industry,
       ROUND(SUM(CASE WHEN sector = 'Ground Transport' THEN mtco2_per_day ELSE 0 END), 1) AS ground_transport,
       ROUND(SUM(CASE WHEN sector = 'Residential'      THEN mtco2_per_day ELSE 0 END), 1) AS residential,
       ROUND(SUM(CASE WHEN sector = 'Domestic Aviation'      THEN mtco2_per_day ELSE 0 END), 1) AS domestic_aviation,
       ROUND(SUM(CASE WHEN sector = 'International Aviation'  THEN mtco2_per_day ELSE 0 END), 1) AS intl_aviation
FROM daily_emissions
GROUP BY country
ORDER BY country;


-- ============================================================
-- 4. Year-over-year % change for EVERY country
-- ------------------------------------------------------------
-- A CTE builds each country's yearly total, then we self-join it to the
-- previous year (matched on same country, year - 1) to compute growth %.
-- One row per country per year — ideal for a Power BI line chart with a
-- country legend.
-- ============================================================
WITH country_year AS (
    SELECT country,
           LEFT(date, 4)                AS year,
           ROUND(SUM(mtco2_per_day), 0) AS total_mtco2
    FROM daily_emissions
    GROUP BY country, LEFT(date, 4)
)
SELECT c.country,
       c.year,
       c.total_mtco2,
       ROUND(100.0 * (c.total_mtco2 - p.total_mtco2) / p.total_mtco2, 2) AS yoy_change_pct
FROM country_year c
LEFT JOIN country_year p
       ON p.country = c.country                       -- same country
      AND CAST(p.year AS INT) = CAST(c.year AS INT) - 1   -- previous year
ORDER BY c.country, c.year;


-- ============================================================
-- 5. Monthly totals for all countries (long format)
-- ------------------------------------------------------------
-- One row per country per month. "Long" shape (not pivoted) is exactly what
-- Power BI likes — drop 'month' on the axis, 'total_mtco2' as the value, and
-- 'country' as the legend to get one line per country.
-- ============================================================
SELECT country,
       LEFT(date, 7)                AS month,
       ROUND(SUM(mtco2_per_day), 1) AS total_mtco2
FROM daily_emissions
GROUP BY country, LEFT(date, 7)
ORDER BY country, month;
