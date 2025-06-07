import pandas as pd
import sqlite3
import os

conn = sqlite3.connect('copd_public_health.db')
cursor = conn.cursor()

data_dir = 'sample_data'
postfix = '' #'_sample'

# Define expected columns - matching the simplified table schema
nhanes_columns = [
    "SEQN",          # Respondent ID
    "MCQ010",        # Ever been told you have asthma
    "MCQ160P",       # Ever been told you had COPD
    "SMQ020",        # Smoked at least 100 cigarettes
    "SMQ040",        # Do you now smoke cigarettes
    "RIAGENDR",      # Gender
    "RIDAGEYR",      # Age at screening
    "RIDRETH1",      # Race/Hispanic origin
    "HIQ011"         # Covered by health insurance
]

# Load NHANES sample
print("Loading NHANES data...")
df_nhanes = pd.read_csv(os.path.join(data_dir, f'nhanes_2021-2023_copd{postfix}.csv'))

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
df_wonder = pd.read_csv(os.path.join(data_dir, f'wonder_2018-2023{postfix}.csv'))

# Map the real CSV columns to the DB column names
df_wonder = df_wonder.rename(columns={
    'State': 'state',
    'Year': 'year',
    'Sex Code': 'sex',
    'Single-Year Ages': 'age',
    'Single Race 6': 'race',
    'ICD-10 113 Cause List': 'cause_of_death',
    'Deaths': 'number_of_deaths'
})

# Aggregate deaths by all primary key columns
print("Aggregating WONDER data...")
df_wonder = df_wonder.groupby([
    'state', 'year', 'sex', 'age', 'race', 'cause_of_death'
])['number_of_deaths'].sum().reset_index()

# Print unique values for key columns to verify data
print("\nWONDER data verification:")
print("Unique years:", sorted(df_wonder['year'].unique()))
print("Unique states:", len(df_wonder['state'].unique()))
print("Unique races:", df_wonder['race'].unique())

# Calculate population (not available in raw data)
# Group by state, year, sex, age, and race to get total deaths
state_totals = df_wonder.groupby([
    'state', 'year', 'sex', 'age', 'race'
])['number_of_deaths'].sum().reset_index()

# For this sample, we'll estimate population as deaths * 1000 (placeholder)
state_totals['population'] = state_totals['number_of_deaths'] * 1000

# Merge population back to main dataframe
df_wonder = df_wonder.merge(
    state_totals[['state', 'year', 'sex', 'age', 'race', 'population']], 
    on=['state', 'year', 'sex', 'age', 'race']
)

# Keep only expected columns
wonder_columns = [
    'state', 'year', 'sex', 'age', 'race', 
    'cause_of_death', 'number_of_deaths', 'population'
]
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
df_places = pd.read_csv(os.path.join(data_dir, f'places_2022{postfix}.csv'), low_memory=False)

# Print column names and sample data to debug
print("\nPLACES raw data info:")
print("Columns:", df_places.columns.tolist())
print("Sample row:")
print(df_places.iloc[0])

# Drop any unnamed columns
df_places = df_places.loc[:, ~df_places.columns.str.contains('^Unnamed')]

# Create a filtered DataFrame for each measure we need
print("\nUnique measures in PLACES data:")
print(df_places['Measure'].unique())

obesity = df_places[
    (df_places['Category'] == 'Health Outcomes') & 
    (df_places['Measure'] == 'Obesity among adults')
].copy()

smoking = df_places[
    (df_places['Measure'] == 'Current cigarette smoking among adults')
].copy()

copd = df_places[
    (df_places['Measure'] == 'Chronic obstructive pulmonary disease among adults')
].copy()

# Print counts for each measure to debug
print("\nMeasure counts:")
print("Obesity records:", len(obesity))
print("Smoking records:", len(smoking))
print("COPD records:", len(copd))

# Create separate DataFrames for each measure
obesity_df = pd.DataFrame({
    'state': obesity['StateAbbr'],
    'county_name': obesity['LocationName'],
    'fips_code': obesity['LocationID'].astype(str),
    'obesity_prevalence': obesity['Data_Value']
})

smoking_df = pd.DataFrame({
    'fips_code': smoking['LocationID'].astype(str),
    'smoking_prevalence': smoking['Data_Value']
})

copd_df = pd.DataFrame({
    'fips_code': copd['LocationID'].astype(str),
    'copd_prevalence': copd['Data_Value']
})

# Merge all measures together
places_processed = obesity_df.merge(
    smoking_df, on='fips_code', how='left'
).merge(
    copd_df, on='fips_code', how='left'
)

# Remove duplicates after merging
places_processed = places_processed.drop_duplicates(subset=['fips_code'], keep='first')

print("\nFinal PLACES data shape:", places_processed.shape)
print("Sample of processed data:")
print(places_processed.head())
print("\nValue counts:")
print("COPD values:", places_processed['copd_prevalence'].notna().sum())
print("Smoking values:", places_processed['smoking_prevalence'].notna().sum())
print("Obesity values:", places_processed['obesity_prevalence'].notna().sum())

# Clear existing PLACES data
print("Clearing existing PLACES data...")
cursor.execute("DELETE FROM places_health")
conn.commit()

print("Inserting new PLACES data...")
places_processed.to_sql('places_health', conn, if_exists='append', index=False)

print("\nLoading EPA air quality data...")
df_aqi = pd.read_csv(os.path.join(data_dir, f'epa_pm25_2010-2024{postfix}.csv'))

# Drop any unnamed columns
df_aqi = df_aqi.loc[:, ~df_aqi.columns.str.contains('^Unnamed')]

# No aggregation needed
print("EPA AQI data shape:", df_aqi.shape)
print("EPA AQI columns:", df_aqi.columns.tolist())
print("Sample of EPA AQI data:")
print(df_aqi.head())

# Clear existing air quality data
print("Clearing existing air quality data...")
cursor.execute("DELETE FROM state_air_quality")
conn.commit()

print("Inserting new air quality data...")
df_aqi.to_sql('state_air_quality', conn, if_exists='append', index=False)

conn.commit()
conn.close()
print("\nAll data loaded successfully!")
