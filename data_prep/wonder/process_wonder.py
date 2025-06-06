import pandas as pd
import glob
import os

# Get all data files
files = glob.glob('*.xls*')

df_list = []
for file in files:
    print(f"\nProcessing {file}...")
    try:
        # First try reading as Excel
        try:
            if file.endswith('.xls'):
                df = pd.read_excel(file, engine='xlrd')
            else:
                df = pd.read_excel(file, engine='openpyxl')
        except Exception as excel_error:
            print(f"Could not read as Excel, trying TSV/CSV format...")
            # Try reading as TSV
            try:
                df = pd.read_csv(file, sep='\t')
            except Exception as tsv_error:
                # Try reading as CSV
                try:
                    df = pd.read_csv(file)
                except Exception as csv_error:
                    raise Exception(f"Failed to read file as Excel, TSV, or CSV: {str(excel_error)}")
        
        print(f"\nInitial DataFrame shape: {df.shape}")
        print("Initial columns:", df.columns.tolist())
        print("\nSample of initial data:")
        print(df.head())
        
        # Drop rows where Notes is not NaN (keeping rows where Notes is NaN)
        if 'Notes' in df.columns:
            print("\nBefore filtering - non-null counts:")
            print(df.count())
            
            # Keep rows where Notes is NaN
            df = df[df['Notes'].isna()]
            print("\nAfter filtering - non-null counts:")
            print(df.count())
            
            # Drop the Notes column
            df = df.drop(columns=['Notes'])
        
        # Extract year from filename
        year = file.split('-')[0]
        df['Year'] = year
        
        # Remove any completely empty rows
        df = df.dropna(how='all')
        
        print("\nFinal DataFrame Info:")
        print(df.info())
        print("\nFinal sample rows:")
        print(df.head())
        
        if not df.empty:
            df_list.append(df)
            print(f"Successfully processed {file}")
        else:
            print(f"Warning: No valid data rows in {file}")
            
    except Exception as e:
        print(f"Error processing {file}: {str(e)}")

if df_list:
    df_concat = pd.concat(df_list)
    
    # Save processed data
    output_file = 'wonder_2018-2023.csv'
    df_concat.to_csv(output_file, index=False)
    print(f"\nData saved to {output_file}")
    
    # Print final DataFrame info
    print("\nFinal Combined DataFrame Info:")
    print(df_concat.info())
    print("\nSample of final data:")
    print(df_concat.head())
else:
    print("\nNo files were successfully processed")
