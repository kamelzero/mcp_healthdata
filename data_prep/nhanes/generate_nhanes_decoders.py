import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

DATA_FILES = [
    "MCQ_L", "SMQ_L", "SMQFAM_L", "ALQ_L", "DIQ_L", "HIQ_L", "RHQ_L",
    "HOQ_L", "DEMO_L", "DBQ_L", "HEQ_L", "DPQ_L", "OCQ_L", "PAQ_L",
    "WHQ_L", "KIQ_U_L"
]

BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/{file}.htm"

variable_labels = {}
value_labels = {}

# Setup headless Chrome
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(options=chrome_options)

for file_code in DATA_FILES:
    url = BASE_URL.format(file=file_code)
    print(f"🔍 Processing {url}")

    max_retries = 2
    for attempt in range(max_retries):
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "pagebreak"))
            )
            break  # success!
        except TimeoutException:
            print(f"⚠️ Timeout on {url}, attempt {attempt+1}/{max_retries}")
            if attempt + 1 == max_retries:
                continue  # move on to next file

    # Wait until at least one .pagebreak element is present
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "pagebreak"))
        )
    except Exception as e:
        print(f"⚠️ Timeout waiting for {url}")
        continue

    divs = driver.find_elements(By.CLASS_NAME, "pagebreak")
    for div in divs:
        try:
            varname = div.find_element(By.CLASS_NAME, "vartitle").get_attribute("id")
            
            dts = div.find_elements(By.TAG_NAME, "dt")
            dds = div.find_elements(By.TAG_NAME, "dd")
            label = None

            for dt, dd in zip(dts, dds):
                if dt.text.strip().startswith("SAS Label"):
                    label = dd.text.strip()
                    break
            
            if not label:
                label = varname  # fallback
            
            variable_labels[varname] = label

            # Parse value table if it exists
            try:
                table = div.find_element(By.TAG_NAME, "table")
                rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # skip header
                for row in rows:
                    tds = row.find_elements(By.TAG_NAME, "td")
                    if len(tds) >= 2:
                        code = tds[0].text.strip()
                        desc = tds[1].text.strip()
                        if code and code not in [".", ""]:
                            value_labels.setdefault(varname, {})[code] = desc
            except:
                continue
        except:
            continue

driver.quit()

# Save as JSON
with open("nhanes_variable_labels.json", "w") as f:
    json.dump(variable_labels, f, indent=2)

with open("nhanes_value_labels.json", "w") as f:
    json.dump(value_labels, f, indent=2)

print(f"✅ Done. Found {len(variable_labels)} variables, {len(value_labels)} with value mappings.")
