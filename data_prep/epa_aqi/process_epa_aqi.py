# process_epa_aqi.py

import pandas as pd
import os

def process_epa_pm25(data_folder, output_file, years):
    all_years_data = []
    
    for year in years:
        print(f"Processing EPA data for year: {year}")
        file_path = os.path.join(data_folder, f'annual_conc_by_monitor_{year}.csv')
        df_pm25 = pd.read_csv(file_path)
        
        # Filter for PM2.5 - Local Conditions
        df_pm25 = df_pm25[df_pm25['Parameter Name'] == 'PM2.5 - Local Conditions']
        
        # Group by State and Year, calculate mean Arithmetic Mean
        df_state_pm25 = df_pm25.groupby(['State Name', 'Year'])['Arithmetic Mean'].mean().reset_index()
        
        # Rename for final output
        df_state_pm25 = df_state_pm25.rename(columns={
            'State Name': 'state',
            'Year': 'year',
            'Arithmetic Mean': 'pm25_annual_mean'
        })
        
        all_years_data.append(df_state_pm25)
    
    # Combine all years
    df_pm25_all = pd.concat(all_years_data, ignore_index=True)
    
    print(f"Saving processed EPA PM2.5 data to {output_file}")
    df_pm25_all.to_csv(output_file, index=False)
    print("Done!")

if __name__ == "__main__":
    # Folder where raw EPA CSVs are stored
    data_folder = '../../data/epa_aqi/'
    
    # Output CSV file
    output_file = os.path.join(data_folder, 'epa_pm25_2010-2024.csv')
    
    # Years you want to process
    years = [2010, 2011, 2012, 2013, 2014, 2015, 2016, 
             2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024]
    
    process_epa_pm25(data_folder, output_file, years)
