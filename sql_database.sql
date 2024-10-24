--SELECT * FROM "mktg_seo_raw"."wcd_website" WHERE DATE = '2024-03-26';
--DELETE FROM mktg_seo_raw.wcd_website;
-- DROP TABLE mktg_seo_raw.wcd_website;

--SELECT SUM(load_time) FROM "mktg_seo_raw"."wcd_website" WHERE DATE = '2024-03-28' AND load_time IS NOT NULL;

--Staging table and long term data store template (and streamlit staging)
CREATE TABLE IF NOT EXISTS mktg_seo_raw.wcd_website (
    date DATE,
    original_url VARCHAR(255),
    page_url VARCHAR(255),
    redirect BOOLEAN,
    status_code INTEGER,
    header_tags TEXT,
    meta_data TEXT,
    meta_description TEXT,
    meta_charset VARCHAR(255),
    web_links TEXT,
    image_url TEXT,
    image_alt TEXT,
    canonical_url VARCHAR(255),
    load_time FLOAT
);

--Persistent broken links table constantly updated after each scrape for broken links
CREATE TABLE IF NOT EXISTS mktg_seo_raw.broken_links(
    date DATE,
    original_url VARCHAR(255),
    status_code INTEGER
);

--daily scrape table for short term data query
CREATE TABLE IF NOT EXISTS mktg_seo_raw.daily_scrape (
    date DATE,
    original_url VARCHAR(255),
    page_url VARCHAR(255),
    status_code INTEGER,
    load_time FLOAT
);

--elements table for short term data query
CREATE TABLE IF NOT EXISTS mktg_seo_raw.wcd_elements(
    original_url VARCHAR(255),
    redirect BOOLEAN,
    header_tags TEXT,
    meta_data TEXT,
    meta_description TEXT,
    meta_charset VARCHAR(255),
    image_url TEXT,
    image_alt TEXT,
    canonical_url VARCHAR(255)
);

--weblinks table for short term data query, unlike other tables this will be filled when creating the janusgraph.
--there will also be a long term storage for weblinks as well
DROP TABLE IF EXISTS mktg_seo_raw.web_links, mktg_seo_raw.web_links_storage;
CREATE TABLE IF NOT EXISTS web_links(
    original_url VARCHAR(255),
    domain_urls TEXT,
    external_urls TEXT,
    anomoly_urls TEXT,
    date DATE
);

-- LONG TERM STORAGE S3, WCD_WEBSITE

/*
CREATE TEMP TABLE mktg_seo_raw.temp_broken_links AS
--use staging status code in case in rare case status code is to be changed
SELECT db1.date, db1.original_url, db2.status_code
FROM mktg_seo_raw.broken_links db1
--Join the current broken links with the scraped broken links 
INNER JOIN mktg_seo_raw.scrape_staging db2 ON db1.original_url = db2.original_url
WHERE db2.status_code >= 400

UNION

SELECT db2.date, db2.original_url, db2.status_code
FROM mktg_seo_raw.scrape_staging db2
LEFT JOIN mktg_seo_raw.broken_links db1 ON db2.original_url = db1.original_url
WHERE db1.original_url IS NULL AND db2.status_code >= 400;

TRUNCATE TABLE mktg_seo_raw.broken_links;

INSERT INTO mktg_seo_raw.broken_links_final (date, original_url, status_code)
SELECT date, original_url, status_code
FROM temp_broken_links;


INSERT INTO mktg_seo_raw.daily_scrape (date, original_url, page_url, status_code, load_time)
SELECT date, original_url, page_url, status_code, load_time
FROM mktg_seo_raw.scrape_staging

INSERT INTO mktg_seo_raw.wcd_elements (original_url, redirect, header_tags, meta_data, meta_description, meta_charset, web_links, image_url, image_alt, canonical_url)
SELECT original_url, redirect, header_tags, meta_data, meta_description, meta_charset, web_links, image_url, image_alt, canonical_url
from mktg_seo_raw.scrape_staging


TRUNCATE TABLE mktg_seo_raw.broken_links_temp;

--use staging status code in case in rare case status code is to be changed
INSERT INTO mktg_seo_raw.broken_links_temp (date, original_url, status_code)
SELECT db1.date, db1.original_url, db2.status_code
FROM mktg_seo_raw.broken_links db1
--Join the current broken links with the scraped broken links 
INNER JOIN mktg_seo_raw.scrape_staging db2 ON db1.original_url = db2.original_url
WHERE db2.status_code >= 300
--Join new broken links
UNION
SELECT db2.date, db2.original_url, db2.status_code
FROM mktg_seo_raw.scrape_staging db2
LEFT JOIN mktg_seo_raw.broken_links db1 ON db2.original_url = db1.original_url
WHERE db1.original_url IS NULL AND db2.status_code >= 300;


TRUNCATE TABLE mktg_seo_raw.broken_links;

INSERT INTO mktg_seo_raw.broken_links (date, original_url, status_code)
SELECT date, original_url, status_code
FROM mktg_seo_raw.broken_links_temp; 
*/