-- schema.sql  (T-SQL for SQL Server)
-- ==================================
-- Defines the database table (DDL = Data Definition Language).
-- Run automatically by src/data/etl.py before loading the data.
-- You can also run it by hand in SSMS against the PAM_CO2 database.

-- Drop the table if it already exists (T-SQL form of "DROP TABLE IF EXISTS")
IF OBJECT_ID('dbo.daily_emissions', 'U') IS NOT NULL
    DROP TABLE dbo.daily_emissions;

-- One row = the emissions of ONE country, ONE sector, on ONE day.
CREATE TABLE dbo.daily_emissions (
    id             INT IDENTITY(1,1) PRIMARY KEY,   -- auto-increment id
    date           VARCHAR(10) NOT NULL,            -- ISO date text: yyyy-mm-dd
    country        VARCHAR(50) NOT NULL,            -- e.g. 'China', 'United States'
    sector         VARCHAR(50) NOT NULL,            -- e.g. 'Power', 'Ground Transport'
    mtco2_per_day  FLOAT       NOT NULL,            -- million tonnes CO2 that day
    CONSTRAINT uq_emission UNIQUE (date, country, sector)   -- no duplicate rows
);

-- Indexes make the common lookups (by date, by country) fast.
CREATE INDEX idx_emissions_date    ON dbo.daily_emissions (date);
CREATE INDEX idx_emissions_country ON dbo.daily_emissions (country);
