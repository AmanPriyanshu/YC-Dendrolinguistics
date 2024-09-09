import json
from gliner import GLiNER
from tqdm.notebook import tqdm

class EntitiesExtractor:
    def __init__(self):
        self.model = GLiNER.from_pretrained("numind/NuNerZero")
        self.labels = ["company name", "industry", "problem", "solution", "technology", "audience", "value prop", "key feature", "innovation", "market task", "adjective", "action verb", "person name"]
        
    def merge_entities(self, entities, text):
        if not entities:
            return []
        merged = []
        current = entities[0]
        for next_entity in entities[1:]:
            if next_entity['label'] == current['label'] and (next_entity['start'] == current['end'] + 1 or next_entity['start'] == current['end']):
                current['text'] = text[current['start']: next_entity['end']].strip()
                current['end'] = next_entity['end']
            else:
                merged.append(current)
                current = next_entity
        merged.append(current)
        return merged
    
    def extract(self, text, thr=0.01):
        entities = self.model.predict_entities(text, self.labels, threshold=thr)
        entities = self.merge_entities(entities, text)
        sorted_entities = sorted(entities, key=lambda x: x['end'])
        sorted_entities = [{k: v for k, v in d.items() if k not in ('start', 'end', 'score')} for d in sorted_entities]
        return sorted_entities
    
    def __call__(self, text):
        return self.extract(text, thr=1/(len(self.labels)-2))
    
def main(input_path, output_path):
    with open(input_path, 'r') as f:
        data = json.load(f)
        
    ee = EntitiesExtractor()

    startup_ner_records = {}
    for startup_name, startup in tqdm(data.items(), total=len(list(data.keys()))):
        short_description = startup.get('short_description')
        description = startup.get('description')
        founder_description = "\n".join([f"{n} {d}" for n, d in startup.get('founders', "").items()])
        tldr_one_sentence = startup.get('tldr_one_sentence')
        setting = startup.get('setting')
        problem = startup.get('problem')
        solution = startup.get('solution')
        startup_ner_records[startup_name] = {}
        if type(short_description)==str and len(short_description)>1:
            startup_ner_records[startup_name]["short_description"] = ee(short_description)
        if type(description)==str and len(description)>1:
            startup_ner_records[startup_name]["description"] = ee(description)
        if type(founder_description)==str and len(founder_description)>1:
            startup_ner_records[startup_name]["founder_description"] = ee(founder_description)
        if type(tldr_one_sentence)==str and len(tldr_one_sentence)>1:
            startup_ner_records[startup_name]["tldr_one_sentence"] = ee(tldr_one_sentence)
        if type(setting)==str and len(setting)>1:
            startup_ner_records[startup_name]["setting"] = ee(setting)
        if type(problem)==str and len(problem)>1:
            startup_ner_records[startup_name]["problem"] = ee(problem)
        if type(solution)==str and len(solution)>1:
            startup_ner_records[startup_name]["solution"] = ee(solution)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(startup_ner_records, f, indent=4)

if __name__=='__main__':
    input_path = 'extracted_content.json'
    output_path = 'startup_ner_records.json'
    main(input_path=input_path, output_path=output_path)