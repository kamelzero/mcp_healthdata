import sqlite3

conn = sqlite3.connect('copd_public_health.db')
cursor = conn.cursor()

# Drop existing tables if they exist
cursor.execute("DROP TABLE IF EXISTS nhanes_survey")
cursor.execute("DROP TABLE IF EXISTS wonder_mortality")
cursor.execute("DROP TABLE IF EXISTS places_health")
cursor.execute("DROP TABLE IF EXISTS state_air_quality")

# Create tables
cursor.execute("""
CREATE TABLE nhanes_survey (
    SEQN INTEGER PRIMARY KEY,          -- Respondent ID
    MCQ010 INTEGER,                    -- Ever been told you have asthma
    MCQ160p INTEGER,                    -- Ever been told you had COPD
    SMQ020 INTEGER,                    -- Smoked at least 100 cigarettes
    SMQ040 INTEGER,                    -- Do you now smoke cigarettes
    RIAGENDR INTEGER,                   -- Gender
    RIDAGEYR INTEGER,                   -- Age at screening
    RIDRETH1 INTEGER,                   -- Race/Hispanic origin
    HIQ011 INTEGER                      -- Covered by health insurance
)""")

cursor.execute("""
CREATE TABLE wonder_mortality (
    state TEXT,                         -- State abbreviation
    year INTEGER,                       -- Year
    sex TEXT,                          -- Gender
    age TEXT,                          -- Age group
    race TEXT,                         -- Race/ethnicity
    cause_of_death TEXT,               -- ICD-10 Cause
    number_of_deaths INTEGER,          -- Number of deaths
    population INTEGER,                -- Population
    PRIMARY KEY (state, year, sex, age, race, cause_of_death)
)""")

cursor.execute("""
CREATE TABLE places_health (
    state TEXT,                         -- State abbreviation
    county_name TEXT,                   -- County name
    fips_code TEXT PRIMARY KEY,         -- County FIPS
    copd_prevalence FLOAT,              -- % COPD prevalence
    smoking_prevalence FLOAT,           -- % smoking prevalence
    obesity_prevalence FLOAT            -- % obesity prevalence
)""")

cursor.execute("""
CREATE TABLE state_air_quality (
    state TEXT,                         -- State abbreviation
    year INTEGER,                       -- Year
    pm25_annual_mean FLOAT,             -- Annual mean PM2.5
    PRIMARY KEY (state, year)
)""")

conn.commit()
conn.close()
