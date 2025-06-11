import os
import pandas as pd


DATA_DIR = "../../data/nhanes/nhanes_xpt_files"
OUTFILE = "../../data/nhanes/nhanes_2021-2023_copd.parquet"

# Survey year for 2021-2023 cycle
SURVEY_YEAR = 2022  # Using middle year of the cycle

FILES = {
    "DEMO": "DEMO_L.xpt",
    "SMQ": "SMQ_L.xpt",
    "SMQFAM": "SMQFAM_L.xpt",
    "MCQ": "MCQ_L.xpt",
    "BPQ": "BPQ_L.xpt",
    "RHQ": "RHQ_L.xpt",
    "HUQ": "HUQ_L.xpt",
    "ALQ": "ALQ_L.xpt",
    "DIQ": "DIQ_L.xpt",
    "HEQ": "HEQ_L.xpt",
    "BMX": "BMX_L.xpt",
    "HSCRP": "HSCRP_L.xpt",
    "GLU": "GLU_L.xpt",
    "GHB": "GHB_L.xpt",
    "INS": "INS_L.xpt",
    "TCHOL": "TCHOL_L.xpt",
    "HIQ": "HIQ_L.xpt",
}

def load_xpt(filename):
    path = os.path.join(DATA_DIR, filename)
    print(f"Loading {filename}...")
    return pd.read_sas(path, format="xport")

def recode_yes_no(series):
    """
    Maps NHANES yes/no variables to 1/0.
    Returns pd.NA for any unexpected values.
    """
    return series.replace({1: 1, 2: 0}).where(series.isin([1, 2]))

def process():
    # Step 1: Load files
    dfs = {}
    for key, fname in FILES.items():
        try:
            dfs[key] = load_xpt(fname)
        except Exception as e:
            print(f"⚠️ Failed to load {fname}: {e}")

    # Step 2: Merge on SEQN
    merged = dfs["DEMO"]
    for key, df in dfs.items():
        if key != "DEMO":
            merged = merged.merge(df, on="SEQN", how="left")

    print(f"✅ Merged shape: {merged.shape}")

    # Add survey year
    merged["year"] = SURVEY_YEAR

    # Step 3: Add derived variables

    # Demographics
    merged["age_group"] = pd.cut(
        merged["RIDAGEYR"], bins=[0, 18, 39, 64, 120],
        labels=["<18", "18–39", "40–64", "65+"]
    )

    # Decode variables
    # from decode_variables import apply_nhanes_labels, value_labels
    # merged = apply_nhanes_labels(merged, value_labels)

    # Smoking
    merged["smoked_100_cigs"] = recode_yes_no(merged["SMQ020"])
    merged["current_smoker"] = merged["SMQ040"].map({
        1: 1,  # Every day
        2: 1,  # Some days
        3: 0,  # Not at all
        7: None,
        9: None
    })
    merged["household_smokers"] = recode_yes_no(merged["SMAQUEX2"])

    # # Respiratory
    merged["asthma_ever"] = recode_yes_no(merged["MCQ010"])
    merged["asthma_now"] = recode_yes_no(merged["MCQ053"])
    merged["bronchitis"] = recode_yes_no(merged["MCQ149"])

    # # Diabetes
    merged["has_diabetes"] = recode_yes_no(merged["DIQ010"])  # Doctor told you?

    # BMI category
    if "BMXBMI" in merged.columns:
        merged["bmi"] = merged["BMXBMI"]
        merged["bmi_category"] = pd.cut(
            merged["BMXBMI"],
            bins=[0, 18.5, 25, 30, 100],
            labels=["Underweight", "Normal", "Overweight", "Obese"]
        )

    # Alcohol (optional — may confound respiratory health)
    merged["drinks_per_week"] = merged["ALQ130"]  # usual drinks/week
    merged["alcohol_use"] = recode_yes_no(merged["ALQ111"])  # Had at least 12 drinks of any type of alcoholic ever?

    # Inflammation marker (HSCRP ≥ 3.0 mg/L = high risk)
    merged["high_crp"] = merged["LBXHSCRP"].apply(lambda x: 1 if x >= 3 else (0 if pd.notna(x) else pd.NA))

    # Save final data
    merged.to_parquet(OUTFILE)
    print(f"💾 Saved enriched dataset to: {OUTFILE}")

if __name__ == "__main__":
    process()
