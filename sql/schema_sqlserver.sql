-- schema_sqlserver.sql
-- ====================
-- SQL SERVER (T-SQL) version of the table definition.
-- Run this in SSMS / Azure Data Studio BEFORE importing the CSV, if you want
-- to run the queries in SQL Server instead of SQLite.
--
-- Steps in SSMS:
--   1. Run this script to create the table.
--   2. Right-click your database -> Tasks -> Import Flat File...
--   3. Choose data/raw/carbon_monitor_daily.csv, map to dbo.daily_emissions.

-- Drop the table if it already exists (T-SQL syntax; SQLite uses DROP TABLE IF EXISTS)
IF OBJECT_ID('dbo.daily_emissions', 'U') IS NOT NULL
    DROP TABLE dbo.daily_emissions;

CREATE TABLE dbo.daily_emissions (
    id             INT IDENTITY(1,1) PRIMARY KEY,   -- auto-increment id
    date           VARCHAR(10) NOT NULL,            -- ISO date text: yyyy-mm-dd
    country        VARCHAR(50) NOT NULL,
    sector         VARCHAR(50) NOT NULL,
    mtco2_per_day  FLOAT       NOT NULL,            -- million tonnes CO2 per day
    CONSTRAINT uq_emission UNIQUE (date, country, sector)
);

-- Indexes to speed up the common lookups
CREATE INDEX idx_emissions_date    ON dbo.daily_emissions (date);
CREATE INDEX idx_emissions_country ON dbo.daily_emissions (country);
