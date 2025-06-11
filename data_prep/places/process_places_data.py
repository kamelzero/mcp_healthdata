import pandas as pd

# Input and output paths
INPUT_FILE = "../../data/places/places_2022.csv"
OUTPUT_FILE = "../../data/places/places_2022_processed.parquet"

# PLACES 2024 release uses 2022 BRFSS data
SURVEY_YEAR = 2022

def process_places_data():
    """Process PLACES county-level data for the database."""
    print(f"Loading PLACES data from {INPUT_FILE}...")
    
    # Read the CSV file
    df = pd.read_csv(INPUT_FILE)
    
    # Add year column
    df["year"] = SURVEY_YEAR
    
    # Select and rename relevant columns
    df_processed = df[[
        "StateAbbr",           # State abbreviation
        "CountyName",          # County name
        "CountyFIPS",          # County FIPS code
        "year",               # Survey year
        "COPD_CrudePrev",     # COPD prevalence
        "CSMOKING_CrudePrev", # Current smoking prevalence
        "OBESITY_CrudePrev",  # Obesity prevalence
    ]].rename(columns={
        "StateAbbr": "state",
        "CountyName": "county_name",
        "CountyFIPS": "fips_code",
        "COPD_CrudePrev": "copd_prevalence",
        "CSMOKING_CrudePrev": "smoking_prevalence",
        "OBESITY_CrudePrev": "obesity_prevalence"
    })
    
    # Convert prevalence columns to float
    for col in ["copd_prevalence", "smoking_prevalence", "obesity_prevalence"]:
        df_processed[col] = pd.to_numeric(df_processed[col], errors="coerce")
    
    print(f"Saving processed data to {OUTPUT_FILE}...")
    df_processed.to_parquet(OUTPUT_FILE)
    print("✅ Done!")

if __name__ == "__main__":
    process_places_data() 