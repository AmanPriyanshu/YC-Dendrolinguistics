import pandas as pd
import requests
import os
import re
from tqdm import tqdm

def fetch_html(url):
    response = requests.get(url)
    return response.text if response.status_code == 200 else None

def save_html(content, path):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def sanitize_filename(name):
    return re.sub(r'[^a-zA-Z0-9]', '-', name)

def scrape_and_save(urls, names, directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    for url, name in tqdm(zip(urls, names), total=len(urls), desc="downloading_startups"):
        filename = sanitize_filename(name) + '.html'
        filepath = os.path.join(directory, filename)
        html_content = fetch_html(url)
        if html_content:
            save_html(html_content, filepath)

if __name__ == "__main__":
    df = pd.read_csv("startup_list.csv")
    urls = df["URL"].tolist()
    names = df["Name"].tolist()
    scrape_and_save(urls, names, "raw_dump")
