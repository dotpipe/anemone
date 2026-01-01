import os
import json

def build_thesaurus_assoc(word_list_path, data_dir, output_path):
    assoc = {}
    # Whitelist of canonical subject files (add/remove as needed)
    whitelist = {
        'algebra.json', 'biology.json', 'calculus.json', 'chemistry.json', 'complex_numbers.json',
        'definitions.json', 'economics.json', 'finance.json', 'geometry.json', 'linear_algebra.json',
        'math.json', 'physics.json', 'probability.json', 'statistics.json', 'thermodynamics.json',
        'trigonometry.json', 'user_drift.json', 'vectors.json', 'code_dictionary.json'
    }
    # Read all words to check
    with open(word_list_path, 'r', encoding='utf-8') as f:
        words = set(line.strip() for line in f if line.strip())
    # For each data file, process one at a time
    for fname in os.listdir(data_dir):
        if fname.endswith('.json') and fname in whitelist:
            classification = fname.replace('.json', '')
            with open(os.path.join(data_dir, fname), 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    for word in data:
                        if word in words:
                            assoc.setdefault(word, []).append(classification)
                except Exception:
                    pass
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(assoc, f, ensure_ascii=False, indent=2)
    print(f'thesaurus_assoc.json written with {len(assoc)} entries.')

if __name__ == '__main__':
    build_thesaurus_assoc('word_freq.txt', 'data', 'thesaurus_assoc.json')
