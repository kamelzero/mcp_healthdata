import argparse
import pandas as pd
import os
import shutil

def main(sample):
    epa_aqi_file = 'data/epa_aqi/epa_pm25_2010-2024.csv'
    nhanes_file = 'data/nhanes/nhanes_2021-2023_copd.parquet'
    places_file = 'data/places/places_2022.csv'
    wonder_file = 'data/wonder/wonder_2018-2023.csv'

    os.makedirs('sample_data', exist_ok=True)

    if sample:
        df_epa_aqi = pd.read_csv(epa_aqi_file)
        df_nhanes = pd.read_parquet(nhanes_file)
        df_places = pd.read_csv(places_file)
        df_wonder = pd.read_csv(wonder_file)

        df_epa_aqi.head().to_csv('sample_data/epa_pm25_2010-2024_sample.csv')
        df_nhanes.head().to_csv('sample_data/nhanes_2021-2023_copd_sample.csv')
        df_places.head().to_csv('sample_data/places_2022_sample.csv')
        df_wonder.head().to_csv('sample_data/wonder_2018-2023_sample.csv')
    else:
        shutil.copy(epa_aqi_file, 'sample_data/epa_pm25_2010-2024.csv')
        pd.read_parquet(nhanes_file).to_csv('sample_data/nhanes_2021-2023_copd.csv')
        shutil.copy(places_file, 'sample_data/places_2022.csv')
        shutil.copy(wonder_file, 'sample_data/wonder_2018-2023.csv')

    shutil.copy('data/nhanes/nhanes_variable_labels.json', 'sample_data/nhanes_variable_labels.json')
    shutil.copy('data/nhanes/nhanes_value_labels.json', 'sample_data/nhanes_value_labels.json')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', action='store_true', help='Sample the datasets')
    args = parser.parse_args()

    main(args.sample)
