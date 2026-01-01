import json
import os

CODE_DICTIONARY_PATH = os.path.join(os.path.dirname(__file__), 'data', 'code_dictionary.json')
PYTHON_COMMAND_PATH = os.path.join(os.path.dirname(__file__), 'python_command_templates.json')

with open(CODE_DICTIONARY_PATH, 'r', encoding='utf-8') as f:
    code_dict = json.load(f)
with open(PYTHON_COMMAND_PATH, 'r', encoding='utf-8') as f:
    py_cmds = json.load(f)

for cmd in py_cmds:
    name = cmd.get('name')
    if name:
        entry = code_dict.setdefault(name, {'synonyms': [], 'antonyms': []})
        if name not in entry['synonyms']:
            entry['synonyms'].append(name)
        if name not in entry['antonyms']:
            entry['antonyms'].append(name)

with open(CODE_DICTIONARY_PATH, 'w', encoding='utf-8') as f:
    json.dump(code_dict, f, indent=2, ensure_ascii=False)
print('Persisted all command names as synonyms and antonyms in code_dictionary.json')
