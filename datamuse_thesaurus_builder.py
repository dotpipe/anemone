def build_thesaurus_assoc(word_list_path, data_dir, output_path):
    import os
    assoc = {}
    # Read all words to check
    with open(word_list_path, 'r', encoding='utf-8') as f:
        words = set(line.strip() for line in f if line.strip())
    # For each data file, process one at a time
    # The classification for each word is the filename (without .json) where it appears
    for fname in os.listdir(data_dir):
        if fname.endswith('.json'):
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
def add_classification_to_definitions(word_list_path, data_dir, definitions_path):
    # Load all data/*.json files and build a mapping from word to classification (filename)
    import os
    word_classification = {}
    for fname in os.listdir(data_dir):
        if fname.endswith('.json'):
            class_name = fname.replace('.json', '')
            with open(os.path.join(data_dir, fname), 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    for word in data:
                        word_classification.setdefault(word, []).append(class_name)
                except Exception:
                    pass
    # Load definitions.json
    with open(definitions_path, 'r', encoding='utf-8') as f:
        definitions = json.load(f)
    # For each word in word_freq.txt, if it has a classification, add it to definitions
    with open(word_list_path, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip()
            if not word:
                continue
            if word in word_classification and word in definitions:
                definitions[word]['classification'] = word_classification[word]
    # Save updated definitions.json
    with open(definitions_path, 'w', encoding='utf-8') as f:
        json.dump(definitions, f, ensure_ascii=False, indent=2)
    print('Classifications added to definitions.json')
import os
def load_progress(progress_file):
    if os.path.exists(progress_file):
        with open(progress_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"last_index": 0}

def save_progress(progress_file, last_index):
    with open(progress_file, 'w', encoding='utf-8') as f:
        json.dump({"last_index": last_index}, f)
def split_word_freq_file():
    with open(WORD_FREQ_PATH, 'r', encoding='utf-8') as f:
        words = [line for line in f]
    n = len(words)
    chunk_size = n // 4
    for i in range(4):
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < 3 else n
        with open(f'word_freq_part{i+1}.txt', 'w', encoding='utf-8') as out:
            out.writelines(words[start:end])
    print('word_freq.txt split into 4 parts.')

import requests
import time
import json
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

WORD_FREQ_PATH = 'word_freq.txt'
OUTPUT_PATH = 'datamuse_thesaurus.json'
BATCH_SIZE = 1500
WAIT_SECONDS = 0

def extract_subjects(prompt):
    # Simple word extraction; customize for your needs
    return [word.lower() for word in prompt.split() if word.isalpha()]

def find_word_in_json_files(word, json_files):
    found_in = []
    for file in json_files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if word in data:
                    found_in.append(file)
        except Exception:
            pass
    return found_in

def get_synonyms(word):
    url = f"https://api.datamuse.com/words?rel_syn={word}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return [item['word'] for item in response.json()]
    except Exception:
        pass
    return []

def build_lookup_json(prompt, word_list_path, output_path):
    subjects = extract_subjects(prompt)
    with open(word_list_path, 'r', encoding='utf-8') as f:
        word_set = set(line.strip().lower() for line in f if line.strip())
    lookup = {}
    for word in subjects:
        if word in word_set:
            lookup[word] = get_synonyms(word)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(lookup, f, ensure_ascii=False, indent=2)
    print(f"Lookup JSON saved to {output_path}")
def main():
    with open(WORD_FREQ_PATH, 'r', encoding='utf-8') as f:
        words = [line.strip() for line in f if line.strip()]

    thesaurus = {}
    for i, word in enumerate(tqdm(words, desc="Processing words")):
        thesaurus[word] = get_synonyms(word)
        if (i + 1) % BATCH_SIZE == 0:
            print(f"Processed {i + 1} words, waiting {WAIT_SECONDS} seconds...")
            time.sleep(WAIT_SECONDS)
        if (i + 1) % 20000 == 0:
            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(thesaurus, f, ensure_ascii=False, indent=2)
            print(f"Partial output written at {i + 1} words.")

    # Final write (in case total is not a multiple of 20000)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(thesaurus, f, ensure_ascii=False, indent=2)

    prompt = input("Enter prompt: ")
    subjects = extract_subjects(prompt)
    with open(WORD_FREQ_PATH, 'r', encoding='utf-8') as f:
        word_set = set(line.strip().lower() for line in f if line.strip())

    # List all data/*.json files
    import os
    data_dir = 'data'
    json_files = [os.path.join(data_dir, fname) for fname in os.listdir(data_dir) if fname.endswith('.json')]

    lookup = {}
    associations = {}
    file_cache = {}
    file_usage = {}
    prompt_count = 0
    def process_synonym(word):
        return word, get_synonyms(word)

    associations = {}
    synonym_results = {}
    # First, get all file associations (single-threaded, fast disk lookup)
    # If processing a part, track progress
    part = None
    for i in range(1, 5):
        if os.path.exists(f'word_freq_part{i}.txt'):
            part = i
            break
    progress_file = f'progress_part{part}.json' if part else None
    progress = load_progress(progress_file) if progress_file else {"last_index": 0}
    start_index = progress["last_index"]

    # Load words for the part or all
    if part:
        with open(f'word_freq_part{part}.txt', 'r', encoding='utf-8') as f:
            words = [line.strip() for line in f if line.strip()]
    else:
        words = subjects

    for idx, word in enumerate(tqdm(words, desc="Associating files")):
        if idx < start_index:
            continue
        if word in word_set:
            found_in = find_word_in_json_files(word, json_files)
            associations[word] = found_in
        # Save progress every 1000 words
        if progress_file and (idx + 1) % 1000 == 0:
            save_progress(progress_file, idx + 1)
    # Save final progress
    if progress_file:
        save_progress(progress_file, len(words))

    # Now, download synonyms in parallel (4 threads)
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_synonym, word): word for word in associations}
        for i, future in enumerate(tqdm(as_completed(futures), total=len(futures), desc="Downloading synonyms")):
            word, synonyms = future.result()
            synonym_results[word] = synonyms
            if (i + 1) % BATCH_SIZE == 0:
                print(f"Processed {i + 1} words, waiting {WAIT_SECONDS} seconds...")
                time.sleep(WAIT_SECONDS)
            if (i + 1) % 20000 == 0:
                with open('word_file_associations.json', 'w', encoding='utf-8') as f:
                    json.dump(associations, f, ensure_ascii=False, indent=2)
                print(f"Partial output written at {i + 1} words.")

    # Final write (in case total is not a multiple of 20000)
    with open('word_file_associations.json', 'w', encoding='utf-8') as f:
        json.dump(associations, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    # Uncomment to split the file, then comment again to avoid re-splitting
    # split_word_freq_file()
    # Uncomment to add classifications to definitions.json
    # add_classification_to_definitions('word_freq.txt', 'data', 'data/definitions.json')
    # Uncomment to build thesaurus_assoc.json
    # build_thesaurus_assoc('word_freq.txt', 'data', 'thesaurus_assoc.json')
    main()
