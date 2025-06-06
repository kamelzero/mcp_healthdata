import pandas as pd
import glob

files = glob.glob('*.csv')

df_list = []
for file in files:
    df = pd.read_csv(file)
    df_list.append(df)

df_concat = pd.concat(df_list)
df_concat.to_csv('epa_aqi_2010-2024.csv', index=False)
