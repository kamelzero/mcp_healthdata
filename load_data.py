import pandas as pd
import sqlite3

conn = sqlite3.connect('copd_public_health.db')
cursor = conn.cursor()

# Define expected columns - matching the simplified table schema
nhanes_columns = [
    "SEQN",          # Respondent ID
    "MCQ010",        # Ever been told you have asthma
    "MCQ160p",       # Ever been told you had COPD
    "SMQ020",        # Smoked at least 100 cigarettes
    "SMQ040",        # Do you now smoke cigarettes
    "RIAGENDR",      # Gender
    "RIDAGEYR",      # Age at screening
    "RIDRETH1",      # Race/Hispanic origin
    "HIQ011"         # Covered by health insurance
]

# Load NHANES sample
print("Loading NHANES data...")
df_nhanes = pd.read_csv('sample_data/nhanes_2021-2023_copd_sample.csv')

# Keep only columns that exist and are in our schema
available_columns = [col for col in nhanes_columns if col in df_nhanes.columns]
print(f"Loading columns: {available_columns}")

df_nhanes = df_nhanes[available_columns]  # Safe subset
print("NHANES data shape:", df_nhanes.shape)
print("NHANES columns:", df_nhanes.columns.tolist())

# Clear existing NHANES data
print("Clearing existing NHANES data...")
cursor.execute("DELETE FROM nhanes_survey")
conn.commit()

print("Inserting new NHANES data...")
df_nhanes.to_sql('nhanes_survey', conn, if_exists='append', index=False)

# Load WONDER data
print("\nLoading WONDER mortality data...")
df_wonder = pd.read_csv('sample_data/wonder_2018-2023_sample.csv')

# Map the real CSV columns to the DB column names
df_wonder = df_wonder.rename(columns={
    'State': 'state',
    'Year': 'year',
    'ICD-10 113 Cause List': 'cause_of_death',
    'Deaths': 'number_of_deaths'
})

# Aggregate deaths by state, year, and cause_of_death
print("Aggregating WONDER data...")
df_wonder = df_wonder.groupby(['state', 'year', 'cause_of_death'])['number_of_deaths'].sum().reset_index()

# Calculate population (not available in raw data)
# Group by state and year to get total deaths per state/year
state_totals = df_wonder.groupby(['state', 'year'])['number_of_deaths'].sum().reset_index()
# For this sample, we'll estimate population as deaths * 1000 (placeholder)
state_totals['population'] = state_totals['number_of_deaths'] * 1000

# Merge population back to main dataframe
df_wonder = df_wonder.merge(state_totals[['state', 'year', 'population']], on=['state', 'year'])

# Keep only expected columns
wonder_columns = ['state', 'year', 'cause_of_death', 'number_of_deaths', 'population']
df_wonder = df_wonder[wonder_columns]

print("\nWONDER data shape:", df_wonder.shape)
print("WONDER data columns:", df_wonder.columns.tolist())
print("Sample of WONDER data:")
print(df_wonder.head())

# Clear existing WONDER data
print("\nClearing existing WONDER data...")
cursor.execute("DELETE FROM wonder_mortality")
conn.commit()

print("Inserting new WONDER data...")
df_wonder.to_sql('wonder_mortality', conn, if_exists='append', index=False)

print("\nLoading PLACES health data...")
df_places = pd.read_csv('sample_data/places_2022_sample.csv')

# Drop any unnamed columns
df_places = df_places.loc[:, ~df_places.columns.str.contains('^Unnamed')]

# Create a filtered DataFrame for each measure we need
obesity = df_places[
    (df_places['Category'] == 'Health Outcomes') & 
    (df_places['Measure'] == 'Obesity among adults')
].copy()

smoking = df_places[
    (df_places['Measure'] == 'Current smoking among adults')
].copy()

copd = df_places[
    (df_places['Measure'] == 'COPD among adults')
].copy()

# Combine the data with exact column names matching the schema
places_processed = pd.DataFrame({
    'state': obesity['StateAbbr'],
    'county_name': obesity['LocationName'],
    'fips_code': obesity['LocationID'].astype(str),
    'obesity_prevalence': obesity['Data_Value'],
    'smoking_prevalence': None,  # Will be filled if data exists
    'copd_prevalence': None,     # Will be filled if data exists
    'median_income': None        # Not available in this dataset
})

# Add smoking prevalence if available
if not smoking.empty:
    smoking_map = dict(zip(smoking['LocationID'], smoking['Data_Value']))
    places_processed['smoking_prevalence'] = places_processed['fips_code'].map(smoking_map)

# Add COPD prevalence if available
if not copd.empty:
    copd_map = dict(zip(copd['LocationID'], copd['Data_Value']))
    places_processed['copd_prevalence'] = places_processed['fips_code'].map(copd_map)

# Ensure all columns are present and in the right order
expected_columns = [
    'state',
    'county_name',
    'fips_code',
    'copd_prevalence',
    'smoking_prevalence',
    'obesity_prevalence',
    'median_income'
]
places_processed = places_processed[expected_columns]

print("PLACES data shape:", places_processed.shape)
print("PLACES columns:", places_processed.columns.tolist())
print("Sample of PLACES data:")
print(places_processed.head())

# Clear existing PLACES data
print("Clearing existing PLACES data...")
cursor.execute("DELETE FROM places_health")
conn.commit()

print("Inserting new PLACES data...")
places_processed.to_sql('places_health', conn, if_exists='append', index=False)

print("\nLoading EPA air quality data...")
df_aqi = pd.read_csv('sample_data/epa_aqi_2010-2024_sample.csv')

# Drop any unnamed columns
df_aqi = df_aqi.loc[:, ~df_aqi.columns.str.contains('^Unnamed')]

# Calculate annual mean PM2.5 from Days PM2.5 (as a proxy since we don't have direct measurements)
# Group by state and year, and calculate the percentage of days with PM2.5 issues
aqi_processed = df_aqi.groupby(['State', 'Year']).agg({
    'Days PM2.5': 'sum',
    'Days with AQI': 'sum'
}).reset_index()

aqi_processed['pm25_annual_mean'] = (aqi_processed['Days PM2.5'] / aqi_processed['Days with AQI']) * 100

# Prepare final DataFrame with correct column names
aqi_processed = pd.DataFrame({
    'state': aqi_processed['State'],
    'year': aqi_processed['Year'],
    'pm25_annual_mean': aqi_processed['pm25_annual_mean']
})

print("AQI data shape:", aqi_processed.shape)
print("AQI columns:", aqi_processed.columns.tolist())
print("Sample of AQI data:")
print(aqi_processed.head())

# Clear existing air quality data
print("Clearing existing air quality data...")
cursor.execute("DELETE FROM state_air_quality")
conn.commit()

print("Inserting new air quality data...")
aqi_processed.to_sql('state_air_quality', conn, if_exists='append', index=False)

conn.commit()
conn.close()
print("\nAll data loaded successfully!")
