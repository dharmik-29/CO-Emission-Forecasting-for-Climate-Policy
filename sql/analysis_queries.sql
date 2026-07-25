-- analysis_queries.sql  (T-SQL for SQL Server)
-- ============================================
-- Analytical queries answering real policy questions. Each query is marked
-- with a '-- name: X' tag so src/data/queries.py can pull it out and run it.
-- You can also run this whole file in SSMS against the PAM_CO2 database.
--
-- Demonstrates: aggregation, GROUP BY, ORDER BY, window functions, CTEs, self-joins.
--
-- NOTE: queries that focus on one country use the literal 'China'. When run
-- through queries.py, that word is auto-replaced with config.TARGET_COUNTRY,
-- so the SQL and the models always match.


-- name: country_totals
-- Which countries emit the most over the whole period? (ranking)
USE PAM_CO2;
SELECT country,
       ROUND(SUM(mtco2_per_day), 1) AS total_mtco2,
       ROUND(AVG(mtco2_per_day), 3) AS avg_sector_day
FROM  daily_emissions
GROUP BY country
ORDER BY total_mtco2 DESC;


-- name: sector_breakdown
-- Within one country, which sectors drive emissions?
-- SUM() OVER () gives the country total so we can compute a % share.
SELECT sector,
       ROUND(SUM(mtco2_per_day), 1)                               AS total_mtco2,
       ROUND(100.0 * SUM(mtco2_per_day)
             / SUM(SUM(mtco2_per_day)) OVER (), 1)                AS pct_of_country
FROM   daily_emissions
WHERE country = 'China'
GROUP BY sector
ORDER BY total_mtco2 DESC;


-- name: monthly_trend
-- How do one country's total emissions evolve month by month?
-- LEFT(date, 7) turns 'yyyy-mm-dd' text into 'yyyy-mm'.
SELECT LEFT(date, 7)                AS month,
       ROUND(SUM(mtco2_per_day), 1) AS total_mtco2
FROM   daily_emissions
WHERE country = 'China'
GROUP BY LEFT(date, 7)
ORDER BY month;


-- name: rolling_30d_avg
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
    FROM   daily_emissions
    WHERE country = 'China'
    GROUP BY date
) AS daily
ORDER BY date;


-- name: yearly_change
-- Is the country's output growing or shrinking each year? (CTE + self-join)
-- LEFT(date, 4) turns 'yyyy-mm-dd' text into the year 'yyyy'.
WITH yearly AS (
    SELECT LEFT(date, 4)               AS year,
           ROUND(SUM(mtco2_per_day), 0) AS total_mtco2
    FROM   daily_emissions
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


-- name: weekday_pattern
-- How much lower are weekend emissions? (transport policy)
-- DATENAME gives the day name; DATEPART(WEEKDAY) orders the days correctly.
SELECT DATENAME(WEEKDAY, CAST(date AS date))          AS weekday,
       ROUND(SUM(mtco2_per_day)
             / COUNT(DISTINCT date), 2)               AS avg_daily_mtco2
FROM   daily_emissions
WHERE country = 'China'
GROUP BY DATENAME(WEEKDAY, CAST(date AS date)),
         DATEPART(WEEKDAY, CAST(date AS date))
ORDER BY DATEPART(WEEKDAY, CAST(date AS date));


-- name: top_emission_days
-- Which specific days had the highest total emissions? (TOP, not LIMIT)
SELECT TOP 5
       date,
       ROUND(SUM(mtco2_per_day), 2) AS daily_total
FROM  daily_emissions
WHERE country = 'China'
GROUP BY date
ORDER BY daily_total DESC;
