-- Database Seed & Metadata Initializer

INSERT OR IGNORE INTO dim_country (country_name, is_domestic) VALUES ('United Kingdom', TRUE);
INSERT OR IGNORE INTO dim_country (country_name, is_domestic) VALUES ('EIRE', FALSE);
INSERT OR IGNORE INTO dim_country (country_name, is_domestic) VALUES ('Germany', FALSE);
INSERT OR IGNORE INTO dim_country (country_name, is_domestic) VALUES ('France', FALSE);
INSERT OR IGNORE INTO dim_country (country_name, is_domestic) VALUES ('Netherlands', FALSE);
