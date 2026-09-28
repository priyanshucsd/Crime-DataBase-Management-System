-- Crime Database Management System: schema
-- Run once on an empty database.

DROP TABLE IF EXISTS cases CASCADE;
DROP TABLE IF EXISTS crimes CASCADE;
DROP TABLE IF EXISTS police_officers CASCADE;
DROP TABLE IF EXISTS victims CASCADE;
DROP TABLE IF EXISTS criminals CASCADE;

CREATE TABLE criminals (
    criminal_id   SERIAL PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    gender        VARCHAR(10) CHECK (gender IN ('Male', 'Female', 'Other')),
    address       VARCHAR(255),
    phone         VARCHAR(15)
);

CREATE TABLE victims (
    victim_id SERIAL PRIMARY KEY,
    name      VARCHAR(100) NOT NULL,
    age       INT CHECK (age > 0 AND age < 120),
    gender    VARCHAR(10) CHECK (gender IN ('Male', 'Female', 'Other')),
    address   VARCHAR(255),
    phone     VARCHAR(15)
);

CREATE TABLE police_officers (
    officer_id     SERIAL PRIMARY KEY,
    name           VARCHAR(100) NOT NULL,
    rank           VARCHAR(50)  NOT NULL,
    phone          VARCHAR(15),
    police_station VARCHAR(100) NOT NULL
);

CREATE TABLE crimes (
    crime_id    SERIAL PRIMARY KEY,
    crime_type  VARCHAR(50)  NOT NULL,
    crime_date  DATE         NOT NULL,
    location    VARCHAR(255) NOT NULL,
    description TEXT,
    criminal_id INT REFERENCES criminals(criminal_id) ON DELETE RESTRICT,
    victim_id   INT NOT NULL REFERENCES victims(victim_id) ON DELETE RESTRICT,
    officer_id  INT NOT NULL REFERENCES police_officers(officer_id) ON DELETE RESTRICT
);

CREATE TABLE cases (
    case_id     SERIAL PRIMARY KEY,
    case_number VARCHAR(30) NOT NULL UNIQUE,
    crime_id    INT NOT NULL REFERENCES crimes(crime_id) ON DELETE CASCADE,
    officer_id  INT NOT NULL REFERENCES police_officers(officer_id) ON DELETE RESTRICT,
    filing_date DATE NOT NULL,
    status      VARCHAR(30) NOT NULL DEFAULT 'Open'
                CHECK (status IN ('Open', 'Under Investigation', 'Solved', 'Closed')),
    description TEXT
);