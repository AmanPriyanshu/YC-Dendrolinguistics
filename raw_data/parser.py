import os
import re
from bs4 import BeautifulSoup
import json
from tqdm import tqdm

def extract_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    content = {}
    current_heading = "no_heading"
    for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
        if element.name.startswith('h'):
            current_heading = element.text.strip()
            content[current_heading] = ""
        elif element.name == 'p':
            if current_heading in content:
                content[current_heading] += element.text.strip() + " "
            else:
                content["no_heading"] = element.text.strip() + " "
    for key, value in content.items():
        content[key] = re.sub(r'\s+', ' ', value).strip()
    return content

def process_directory(directory):
    all_content = {}
    filenames = sorted(list(os.listdir(directory)))
    for filename in tqdm(filenames):
        if filename.endswith(".html"):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            content = extract_content(html_content)
            all_content[filename] = content
    return all_content

if __name__=='__main__':
    raw_dump_dir = "raw_dump"
    result = process_directory(raw_dump_dir)
    output_file = "raw_extracted_content.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    print(f"Content extracted and saved to {output_file}")