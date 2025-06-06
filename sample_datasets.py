import pandas as pd
import os
import shutil

df_epa_aqi = pd.read_csv('data/epa_aqi/epa_aqi_2010-2024.csv')
df_nhanes = pd.read_parquet('data/nhanes/nhanes_2021-2023_copd.parquet')
df_places = pd.read_csv('data/places/places_2022.csv')
df_wonder = pd.read_csv('data/wonder/wonder_2018-2023.csv')

os.makedirs('sample_data', exist_ok=True)
df_epa_aqi.head().to_csv('sample_data/epa_aqi_2010-2024_sample.csv')
df_nhanes.head().to_csv('sample_data/nhanes_2021-2023_copd_sample.csv')
df_places.head().to_csv('sample_data/places_2022_sample.csv')
df_wonder.head().to_csv('sample_data/wonder_2018-2023_sample.csv')

shutil.copy('data/nhanes/nhanes_variable_labels.json', 'sample_data/nhanes_variable_labels.json')
shutil.copy('data/nhanes/nhanes_value_labels.json', 'sample_data/nhanes_value_labels.json')
