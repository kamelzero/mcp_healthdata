import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from tqdm import tqdm
# URL for the NHANES 2021-2023 questionnaire data
BASE_URL_LIST = [
    "https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Demographics&Cycle=2021-2023",
    "https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Dietary&Cycle=2021-2023",
    "https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Examination&Cycle=2021-2023",
    "https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Laboratory&Cycle=2021-2023",
    "https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Questionnaire&Cycle=2021-2023"]
DOWNLOAD_DIR = "../../data/nhanes/nhanes_xpt_files"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def fetch_xpt_links(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all links ending in '.XPT'
    xpt_links = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag['href']
        if href.lower().endswith(".xpt"):
            full_url = urljoin(url, href)
            xpt_links.append(full_url)
    return xpt_links

def download_file(url, dest_folder):
    os.makedirs(dest_folder, exist_ok=True)
    local_filename = os.path.join(dest_folder, os.path.basename(url))
    if os.path.exists(local_filename):
        print(f"[SKIP] {local_filename} already exists.")
        return
    print(f"[DOWNLOAD] {url}")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"[SAVED] to {local_filename}")

def main():
    for idx, BASE_URL in enumerate(BASE_URL_LIST):
        print(f"[{idx+1}/{len(BASE_URL_LIST)}] Fetching .XPT files from {BASE_URL}")
        xpt_urls = fetch_xpt_links(BASE_URL)
        print(f"Found {len(xpt_urls)} .XPT files.")
        for url in tqdm(xpt_urls, desc="Downloading .XPT files"):
            download_file(url, DOWNLOAD_DIR)

if __name__ == "__main__":
    main()
