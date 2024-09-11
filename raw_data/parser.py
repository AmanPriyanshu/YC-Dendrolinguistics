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

def process_startup(startup_data):
    result = {}
    result['name'] = next(iter(startup_data.keys()))
    keys = list(startup_data[result['name']].keys())
    if len(keys) > 1:
        result['short_description'] = keys[1][:50]
        result['description'] = startup_data[result['name']][keys[1]]
    result['founders'] = {}
    founder_section = False
    for key, value in startup_data[result['name']].items():
        if key == "Active Founders":
            founder_section = True
            continue
        if key == "Company Launches":
            break
        if founder_section and value:
            result['founders'][key] = value
    company_launches_found = False
    for key, value in startup_data[result['name']].items():
        if key == "Company Launches":
            company_launches_found = True
            continue
        if company_launches_found:
            if 'tldr_one_sentence' not in result:
                result['tldr_one_sentence'] = key
                result['setting'] = value
            break
    for key, value in startup_data[result['name']].items():
        lower_key = key.lower()
        if 'problem' in lower_key:
            result['problem'] = value
        elif 'solution' in lower_key:
            result['solution'] = value
    return result

def clean_raw_extracted_content(input_filepath):
    with open(input_filepath, "r", encoding='utf-8') as f:
        content = json.load(f)
    processed_startups = {}
    for startup_name, startup_info in tqdm(content.items(), total=len(list(content.keys())), desc="cleaning_scraped_data"):
        processed_startups[startup_name] = process_startup({startup_name: startup_info})
    return processed_startups

if __name__=='__main__':
    cleaned_output_file = "extracted_content.json"
    output_file = "raw_extracted_content.json"
    raw_dump_dir = "raw_dump"
    EXTRACT_RAW = False
    if EXTRACT_RAW:
        result = process_directory(raw_dump_dir)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=4, ensure_ascii=False)
        print(f"Content extracted and saved to {output_file}")
    processed_startups = clean_raw_extracted_content(output_file)
    with open(cleaned_output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_startups, f, indent=4, ensure_ascii=False)