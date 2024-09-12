import json
import os
import torch
from tqdm import tqdm
import numpy as np
from transformers import AutoModel, AutoTokenizer

def combine_startup_text(startup_details):
    contents = []
    for value in startup_details.values():
        if isinstance(value, str):
            contents.append(value)
        elif isinstance(value, dict):
            contents.extend(value.values())
    combined_text = ' '.join(contents)
    return combined_text

def split_text_into_windows(text, tokenizer, window_size):
    tokens = tokenizer.encode(text, add_special_tokens=False)
    windows = [tokens[i:i + window_size] for i in range(0, len(tokens), window_size)]
    window_texts = [tokenizer.decode(window, skip_special_tokens=True) for window in windows]
    return window_texts

def process_startups(startup_data, tokenizer, model, batch_size, window_size):
    startup_embeddings = {}
    for startup_name, startup_details in tqdm(startup_data.items(), total=len(list(startup_data.keys())), desc="creating_embeddings"):
        combined_text = combine_startup_text(startup_details)
        window_texts = split_text_into_windows(combined_text, tokenizer, window_size)
        batches = [window_texts[i:i + batch_size] for i in range(0, len(window_texts), batch_size)]
        startup_embs = []
        for batch in batches:
            inputs = tokenizer(batch, padding=True, truncation=True, return_tensors='pt', max_length=window_size)
            with torch.no_grad():
                embs = model(**inputs)[0][:, 0]
                embs = embs.cpu().numpy()
            startup_embs.append(embs)
        if startup_embs:
            startup_embs = np.concat(startup_embs, axis=0).tolist()
            startup_embeddings[startup_name] = startup_embs
    return startup_embeddings

tokenizer = AutoTokenizer.from_pretrained('Snowflake/snowflake-arctic-embed-xs')
model = AutoModel.from_pretrained('Snowflake/snowflake-arctic-embed-xs', add_pooling_layer=False)
model.eval()
batch_size = 8 
window_size = 512

with open(os.path.join("data", "extracted_content.json"), "r", encoding="utf-8") as f:
    startup_data = json.load(f)

startup_embeddings = process_startups(startup_data, tokenizer, model, batch_size, window_size)
with open("document_embeddings.json", "w", encoding="utf-8") as f:
    json.dump(startup_embeddings, f)