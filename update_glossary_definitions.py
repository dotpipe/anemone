import json
import os

def update_glossary_key(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Only keep top-level keys with a definition
    glossary = [k for k, v in data.items() if isinstance(v, dict) and 'definition' in v]
    data['glossary'] = glossary
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Updated glossary key in {json_path} with {len(glossary)} defined words.")

if __name__ == '__main__':
    update_glossary_key('data/definitions.json')
