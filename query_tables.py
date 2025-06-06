import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect('copd_public_health.db')

# Create a function to run queries and display results nicely
def run_query(query, description):
    print(f"\n{description}")
    print("-" * 80)
    result = pd.read_sql_query(query, conn)
    print(result)
    print()

# Count rows in each table
run_query("""
SELECT 
    'nhanes_survey' as table_name, 
    COUNT(*) as row_count 
FROM nhanes_survey
UNION ALL
SELECT 
    'wonder_mortality' as table_name, 
    COUNT(*) as row_count 
FROM wonder_mortality
UNION ALL
SELECT 
    'places_health' as table_name, 
    COUNT(*) as row_count 
FROM places_health
UNION ALL
SELECT 
    'state_air_quality' as table_name, 
    COUNT(*) as row_count 
FROM state_air_quality
""", "Row counts for all tables:")

# NHANES Survey Statistics
run_query("""
SELECT 
    COUNT(*) as total_respondents,
    SUM(CASE WHEN MCQ160p = 1 THEN 1 ELSE 0 END) as copd_count,
    SUM(CASE WHEN SMQ020 = 1 THEN 1 ELSE 0 END) as smokers_count,
    AVG(RIDAGEYR) as avg_age
FROM nhanes_survey
""", "NHANES Survey Statistics:")

# WONDER Mortality Statistics
run_query("""
SELECT 
    year,
    COUNT(DISTINCT state) as num_states,
    SUM(number_of_deaths) as total_deaths,
    AVG(population) as avg_state_population
FROM wonder_mortality
GROUP BY year
ORDER BY year
""", "WONDER Mortality Statistics by Year:")

# PLACES Health Statistics
run_query("""
SELECT 
    COUNT(DISTINCT state) as num_states,
    COUNT(DISTINCT county_name) as num_counties,
    AVG(copd_prevalence) as avg_copd_prevalence,
    AVG(smoking_prevalence) as avg_smoking_prevalence,
    AVG(obesity_prevalence) as avg_obesity_prevalence
FROM places_health
""", "PLACES Health Statistics:")

# Air Quality Statistics
run_query("""
SELECT 
    year,
    COUNT(DISTINCT state) as num_states,
    AVG(pm25_annual_mean) as avg_pm25,
    MIN(pm25_annual_mean) as min_pm25,
    MAX(pm25_annual_mean) as max_pm25
FROM state_air_quality
GROUP BY year
ORDER BY year
""", "Air Quality Statistics by Year:")

# Close the connection
conn.close() 