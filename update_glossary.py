import os
import json
import re
import nltk
from collections import defaultdict
from nltk import word_tokenize, pos_tag

# Download NLTK data if not already present
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

# Define parts of speech to keep (nouns, verbs, predicates)
KEEP_POS = {'NN', 'NNS', 'NNP', 'NNPS', 'VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'}

# Common prepositions, conjunctions, and stopwords to exclude
EXCLUDE_WORDS = set([
    'and', 'or', 'but', 'if', 'while', 'as', 'because', 'before', 'after', 'since', 'until', 'although',
    'though', 'unless', 'whereas', 'so', 'for', 'nor', 'yet', 'with', 'at', 'by', 'from', 'into', 'on',
    'to', 'in', 'of', 'off', 'over', 'under', 'about', 'against', 'between', 'without', 'within', 'through',
    'during', 'including', 'upon', 'among', 'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being'
])

# Directory containing the JSON files
data_dir = os.path.join(os.path.dirname(__file__), 'data')

# Regex to split on non-word characters
splitter = re.compile(r"\W+")

def extract_words(text):
    words = word_tokenize(text)
    tagged = pos_tag(words)
    filtered = [w.lower() for w, pos in tagged if pos in KEEP_POS and w.lower() not in EXCLUDE_WORDS and w.isalpha()]
    return filtered

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    word_set = set()
    for key, entries in data.items():
        # Key as term
        word_set.update(extract_words(key))
        # Each entry may be a dict or list of dicts
        if isinstance(entries, dict):
            entries = [entries]
        for entry in entries:
            for field in ('gloss', 'definition', 'name'):
                if field in entry and isinstance(entry[field], str):
                    word_set.update(extract_words(entry[field]))
            # Synonyms/antonyms fields
            for field in ('synonyms', 'antonyms'):
                if field in entry and isinstance(entry[field], list):
                    for syn in entry[field]:
                        if isinstance(syn, str):
                            word_set.update(extract_words(syn))
    # Add glossary key
    data['glossary'] = sorted(word_set)
    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Updated {os.path.basename(filepath)} with {len(word_set)} unique words.")

if __name__ == '__main__':
    for fname in os.listdir(data_dir):
        if fname.endswith('.json'):
            process_file(os.path.join(data_dir, fname))
