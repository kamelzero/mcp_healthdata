# Download Data

Visit https://aqs.epa.gov/aqsweb/airdata/download_files.html
and for years 2010-2024 download the zip files under column "Concentration by Monitor".

```
for file in *.zip; do unzip "$file"; done
rm ./*zip
```

