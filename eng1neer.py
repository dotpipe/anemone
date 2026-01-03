def is_participle(word):
    # Heuristic: participles often end with these suffixes
    return word.lower().endswith((
        'ing', 'ed', 'en', 'nt', 'd', 't', 'n', 'ne', 'wn', 'pt', 'st', 'ft', 'ld', 'lt', 'rt', 'rd', 'rn', 'rk', 'rm', 'mp', 'nd', 'nt', 'sk', 'sp', 'st', 'th', 'wn', 'zz', 'ss', 'sh', 'ch', 'ph', 'gh', 'wh', 'ng', 'nk', 'ct', 'ft', 'pt', 'xt', 'zz', 'ed', 'en'
    ))

def strip_participles_from_end(text):
    # Remove trailing participles from the end of a sentence
    words = text.rstrip().split()
    while words and is_participle(words[-1].strip('.,;:')):
        words.pop()
    return ' '.join(words)

def respond_subject_specific(prompt: str, assoc_path='thesaurus_assoc.json', data_dir='data') -> str:
    # --- Context-aware answer splicing ---
    # If previous answer exists, use it as context for the next answer
    if not hasattr(respond_subject_specific, '_last_answer'):
        respond_subject_specific._last_answer = ''
    previous_answer = respond_subject_specific._last_answer

    """
    For each extracted term in the prompt, find all subject files (classifications) it appears in using thesaurus_assoc.json.
    Load only those files, gather definitions for the term, and build a subject-specific response.
    """
    import json, os, re
    # --- Normalization helper ---
    # Ensures consistent, lowercase, alphanumeric term matching
    def normalize(term):
        """Normalize a term to lowercase alphanumeric for consistent matching."""
        return re.sub(r'[^a-z0-9]', '', term.lower())

    # --- Association loading ---
    # Loads the main subject association file for fast lookup
    with open(assoc_path, 'r', encoding='utf-8') as f:
        assoc = json.load(f)

    # --- Term extraction and similarity import ---
    # Extracts candidate terms from the prompt and prepares Levenshtein similarity
    import sys
    sys.path.append(os.path.dirname(__file__))
    try:
        from util_word_topic_lookup import similarity
    except ImportError:
        similarity = None
    # --- Persistent subject memory ---
    if not hasattr(respond_subject_specific, "_last_subject"):
        respond_subject_specific._last_subject = None
    terms = extract_terms(prompt)
    # Find the first noun (regular/proper) in the prompt
    import string
    prompt_tokens = re.findall(r"\b\w+\b", prompt)
    def is_noun_candidate(word):
        return word and word[0].isalpha() and word.lower() not in {"i","me","my","mine","myself","you","your","yours","yourself","yourselves","he","him","his","himself","she","her","hers","herself","it","its","itself","we","us","our","ours","ourselves","they","them","their","theirs","themselves","this","that","these","those","who","whom","whose","which","what","where","when","why","how"}
    noun_in_prompt = next((w for w in prompt_tokens if is_noun_candidate(w)), None)
    if noun_in_prompt:
        respond_subject_specific._last_subject = noun_in_prompt
    current_subject = respond_subject_specific._last_subject

    # --- Domain lineage and sibling/subspecies logic ---
    # For each filtered term, find its subject (file), type (term), synonyms (subspecies), and siblings (other terms in file)
    domain_info = {}
    for fname in os.listdir(data_dir):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(data_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as fjson:
                data = json.load(fjson)
        except Exception:
            continue
        for term in terms:
            if term in data:
                entry = data[term]
                # Synonyms (subspecies)
                subspecies = set()
                if isinstance(entry, list):
                    for e in entry:
                        if isinstance(e, dict) and 'synonyms' in e:
                            subspecies.update(e['synonyms'])
                elif isinstance(entry, dict) and 'synonyms' in entry:
                    subspecies.update(entry['synonyms'])
                # Siblings (other types in the same file)
                siblings = [k for k in data.keys() if k != term]
                domain_info[term] = {
                    'kingdom': fname.replace('.json',''),
                    'type': term,
                    'subspecies': sorted(list(subspecies)),
                    'siblings': siblings[:10]  # limit to 10 for brevity
                }


    # --- Prioritized lookup order for subject association ---
    # 1. Direct match in thesaurus_assoc.json
    # 2. Fuzzy match in word_freq.txt (Levenshtein)
    # 3. Direct match in any data/*.json file
    # 4. Direct match in code_dictionary.json
    # 5. Direct match in definitions.json
    # This order ensures the most relevant, subject-specific, and expressive definitions are used first.
    with open(assoc_path, 'r', encoding='utf-8') as f:
        assoc = json.load(f)
    filtered_terms = []
    for term in terms:
        term_l = term.lower().strip()
        # --- 1. Direct subject association ---
        if term_l in assoc:
            filtered_terms.append(term_l)
            continue
        # --- 2. Fuzzy word match (Levenshtein) ---
        word_freq_path = os.path.join(os.path.dirname(__file__), 'word_freq.txt')
        with open(word_freq_path, 'r', encoding='utf-8') as wf:
            word_freq = [line.strip().lower() for line in wf if line.strip()]
        best_match = None
        best_score = 0.0
        if similarity:
            for wf_word in word_freq:
                score = similarity(term_l, wf_word)
                if score > best_score:
                    best_score = score
                    best_match = wf_word
        if best_score >= 0.8:
            # If Levenshtein match, re-check thesaurus_assoc for the matched word
            if best_match in assoc:
                filtered_terms.append(best_match)
                continue
        # --- 3. Direct match in any data/*.json file ---
        found_in_data = False
        for fname in os.listdir(data_dir):
            if fname.endswith('.json'):
                fpath = os.path.join(data_dir, fname)
                try:
                    with open(fpath, 'r', encoding='utf-8') as fjson:
                        data = json.load(fjson)
                    if term_l in data:
                        filtered_terms.append(term_l)
                        found_in_data = True
                        break
                except Exception:
                    continue
        if found_in_data:
            continue
        # --- 4. code_dictionary.json ---
        code_dict_path = os.path.join(data_dir, 'code_dictionary.json')
        if os.path.exists(code_dict_path):
            with open(code_dict_path, 'r', encoding='utf-8') as fcd:
                code_dict = json.load(fcd)
            if term_l in code_dict:
                filtered_terms.append(term_l)
                continue
        # --- 5. definitions.json ---
        definitions_path = os.path.join(data_dir, 'definitions.json')
        if os.path.exists(definitions_path):
            with open(definitions_path, 'r', encoding='utf-8') as fd:
                definitions = json.load(fd)
            if term_l in definitions:
                filtered_terms.append(term_l)
                continue
        # --- If not found anywhere, skip this term ---
    if not filtered_terms:
        return "No subject-specific definitions found for your query."
    terms = filtered_terms
    alt_terms = set(terms)
    responses = []
    import collections
    # Helper: blend multiple definitions with staleness detection
    def blend_definitions(def_list, subject=None):
        """
        Blend a list of definition strings into a single output.
        If a definition is stale (does not mention the subject or drifts off-topic), close it off early.
        """
        if not def_list:
            return ""
        import re
        # 100+ function words that cannot end a sentence
        forbidden_endings = set([
            'about','above','across','after','against','along','amid','among','around','as','at','because','before','behind','below','beneath','beside','besides','between','beyond','but','by','concerning','considering','despite','down','during','except','following','for','from','in','including','inside','into','like','minus','near','of','off','on','onto','opposite','out','outside','over','past','per','plus','regarding','round','save','since','than','through','to','toward','towards','under','underneath','unlike','until','up','upon','versus','via','with','within','without','aboard','alongside','amidst','amongst','apropos','athwart','barring','circa','cum','excepting','excluding','failing','notwithstanding','pace','pending','pro','qua','re','sans','than','throughout','till','times','upon','vis-à-vis','whereas','whether','yet',
            'and','or','nor','so','for','yet','although','because','since','unless','until','while','whereas','though','lest','once','provided','rather','than','that','though','till','unless','until','when','whenever','where','wherever','whether','while','both','either','neither','not','only','but','also','even','if','just','still','then','too','very','well','now','however','thus','therefore','hence','moreover','furthermore','meanwhile','otherwise','besides','indeed','instead','likewise','next','still','then','yet','again','already','always','anyway','anywhere','everywhere','nowhere','somewhere','here','there','where','why','how','whose','which','what','who','whom','whichever','whatever','whoever','whomever',
            'a','an','the','this','that','these','those','my','your','his','her','its','our','their','whose','each','every','either','neither','some','any','no','other','another','such','much','many','more','most','several','few','fewer','least','less','own','same','enough','all','both','half','one','two','three','first','second','next','last','another','certain','various','which','what','whose','whichever','whatever','whoever','whomever','somebody','someone','something','anybody','anyone','anything','everybody','everyone','everything','nobody','noone','nothing','one','oneself','ones','myself','yourself','himself','herself','itself','ourselves','yourselves','themselves','who','whom','whose','which','that','whichever','whatever','whoever','whomever'
        ])
        determiners = ["this", "that", "these", "those", "the", "a", "an"]
        third_person_pronouns = ["he", "she", "it", "they"]
        used_pronoun = False
        def ends_with_forbidden(s):
            words = s.rstrip('.').split()
            return words and words[-1].lower() in forbidden_endings
        def ends_with_noun(s):
            # Heuristic: ends with a word that is not forbidden or a participle
            words = s.rstrip('.').split()
            if not words:
                return False
            last = words[-1].lower()
            if last in forbidden_endings or is_participle(last):
                return False
            return True
        def clean_sentence(s):
            # Remove trailing forbidden words and participles
            words = s.rstrip('.').split()
            while words and (words[-1].lower() in forbidden_endings or is_participle(words[-1])):
                words.pop()
            return ' '.join(words)
        def noun_phrase(noun):
            # Use a determiner for singular, 'the' for plural or known
            if not noun:
                return ''
            if noun.endswith('s') and not noun.endswith('ss'):
                return f"the {noun}"
            return f"a {noun}"
        def append_poignant_subject(s, subj):
            # Add a new sentence with the subject for poignancy, only once
            if not subj:
                return s
            return s.rstrip('.') + f". {subj.capitalize()}."
        # --- Circular, non-hardcoded blend ---
        import random
        if not def_list:
            return ""
        # Clean and split all fragments
        # Store and expose fragments for restoration
        fragments = [clean_sentence(strip_participles_from_end(d.strip())) for d in def_list if d.strip()]
        fragments = [f for f in fragments if f]
        if not fragments:
            blend_definitions._last_fragments = []
            return ""
        blend_definitions._last_fragments = fragments.copy()
        # Use the remembered subject if not provided
        if subject is None and hasattr(respond_subject_specific, "_last_subject"):
            subject = respond_subject_specific._last_subject
        # Find the fragment with the subject or noun phrase
        anchor_idx = 0
        if subject:
            subj_l = subject.lower()
            for i, frag in enumerate(fragments):
                if subj_l in frag.lower():
                    anchor_idx = i
                    break
        # Move anchor to front, wrap tail if needed
        ordered = fragments[anchor_idx:] + fragments[:anchor_idx]
        # Remove duplicate subject mentions in other fragments
        if subject:
            subj_l = subject.lower()
            for i in range(1, len(ordered)):
                if subj_l in ordered[i].lower():
                    ordered[i] = ordered[i].replace(subject, '').replace(subject.capitalize(), '').strip(', .')
        # Join with commas and conjunctions
        if len(ordered) == 1:
            s = ordered[0]
        elif len(ordered) == 2:
            s = f"{ordered[0]}, and {ordered[1]}"
        else:
            s = ', '.join(ordered[:-1]) + f", and {ordered[-1]}"
        s = s.strip(', .')
        # Capitalize and ensure subject is present
        if subject and not s.lower().startswith(subject.lower()):
            s = f"{subject.capitalize()} is {s[0].lower() + s[1:]}"
        else:
            s = s[0].upper() + s[1:]
        # Final clean-up: avoid forbidden endings, add noun phrase if needed
        if ends_with_forbidden(s) and subject:
            s = s + ' ' + noun_phrase(subject)
        if not ends_with_noun(s) and subject:
            s = s + ' ' + noun_phrase(subject)
        if not ends_with_noun(s) and subject:
            s = append_poignant_subject(s, noun_phrase(subject))
        return s.strip()
        if len(def_list) == 1:
            s = strip_participles_from_end(def_list[0])
            s = clean_sentence(s)
            return s
        output = []
        subject = subject.lower() if subject else None
        stale_phrase = " (definition ends here due to lack of subject relevance)"
        for d in def_list:
            d_stripped = d.strip()
            # Staleness: if subject is not mentioned in the last 15 words, or definition is too generic
            last_words = d_stripped.lower().split()[-15:]
            if subject and subject not in last_words and (len(d_stripped) > 40):
                d_stripped = clean_sentence(d_stripped)
                output.append(d_stripped + stale_phrase)
                break
            d_stripped = clean_sentence(d_stripped)
            output.append(d_stripped)
        # Join, then ensure the result ends on a noun/clarifier
        blended = ' '.join(output)
        blended = clean_sentence(blended)
        # If the last word is not a noun, try to append a clarifier and the subject noun
        if not ends_with_noun(blended) and subject:
            blended = blended + f" {subject}"
        return blended.strip()

    # Define file priority order (customize as needed)
    file_priority = [
        # Math group
        'algebra.json', 'linear_algebra.json', 'calculus.json',
        # Science group
        'biology.json', 'chemistry.json', 'physics.json', 'math.json', 'geometry.json', 'complex_numbers.json',
        'probability.json', 'statistics.json', 'thermodynamics.json', 'trigonometry.json', 'vectors.json',
        # Other
        'economics.json', 'finance.json', 'user_drift.json',
        # Code just before definitions
        'code_dictionary.json',
        # Always last
        'definitions.json'
    ]
    # Always include definitions.json last, even if not in file_priority
    files_in_dir = set(f for f in os.listdir(data_dir) if f.endswith('.json'))
    ordered_files = [f for f in file_priority if f in files_in_dir]
    if 'definitions.json' in files_in_dir and 'definitions.json' not in ordered_files:
        ordered_files.append('definitions.json')

    # Build a mapping: term -> [files that define it]
    term_to_files = {term: [] for term in terms}
    file_to_terms = {fname: set() for fname in ordered_files}
    file_term_defs = {fname: {} for fname in ordered_files}
    for fname in ordered_files:
        fpath = os.path.join(data_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as fjson:
                data = json.load(fjson)
            for term in terms:
                entry = data.get(term)
                if entry:
                    term_to_files[term].append(fname)
                    file_to_terms[fname].add(term)
                    file_term_defs[fname][term] = entry
        except Exception:
            continue

    # Prefer to use the file that covers the most terms in the prompt
    # If a term is only found in one file, use that file for that term
    # Otherwise, try to use the file that covers the most terms for as many as possible
    # If tie, use file_priority order
    responses = []
    # Find the file that covers the most terms
    file_term_count = {fname: len(terms_set) for fname, terms_set in file_to_terms.items()}
    # For each term, decide which file to use
    chosen_files = {}
    # First, assign unique files for terms only found in one file
    for term, files in term_to_files.items():
        if len(files) == 1:
            chosen_files[term] = files[0]
    # For remaining terms, try to assign the file that covers the most terms
    remaining_terms = [term for term in terms if term not in chosen_files]
    if remaining_terms:
        # Find the file(s) with max coverage
        max_count = 0
        best_files = []
        for fname in ordered_files:
            count = len(file_to_terms[fname].intersection(remaining_terms))
            if count > max_count:
                max_count = count
                best_files = [fname]
            elif count == max_count and count > 0:
                best_files.append(fname)
        # Use the first best file in priority order
        if best_files:
            best_file = best_files[0]
            for term in remaining_terms:
                if term in file_to_terms[best_file]:
                    chosen_files[term] = best_file
    # For any still unassigned, use the first file in priority order that defines it
    for term in terms:
        if term not in chosen_files:
            files = term_to_files[term]
            if files:
                chosen_files[term] = files[0]
    import difflib
    def is_good_definition(defn, term=None):
        # At least 4 characters, not just a substring or abbreviation of the term, not empty, not just a prefix
        if not defn or len(defn.strip()) < 4:
            return False
        defn_l = defn.strip().lower()
        if term:
            t_l = term.lower()
            # Exclude if definition is a substring, prefix, or abbreviation of the term
            if defn_l == t_l or defn_l in t_l or t_l in defn_l or defn_l.startswith(t_l) or t_l.startswith(defn_l):
                return False
        return True

    # --- Group definitions for Levenshtein fallback ---
    group_map = {
        'math': {'algebra.json', 'linear_algebra.json', 'calculus.json', 'math.json', 'geometry.json', 'complex_numbers.json', 'probability.json', 'statistics.json', 'trigonometry.json', 'vectors.json'},
        'science': {'biology.json', 'chemistry.json', 'physics.json', 'thermodynamics.json'},
        'code': {'code_dictionary.json'},
        'definitions': {'definitions.json'},
        'other': {'economics.json', 'finance.json', 'user_drift.json'}
    }
    def get_group(fname):
        for group, files in group_map.items():
            if fname in files:
                return group
        return 'other'

    # Replace each word in the prompt with its subject-specific definition tidbit
    prompt_tokens = re.findall(r"\b\w+\b", prompt)
    token_defs = {}
    # --- Taxonomy-aware source selection ---
    prompt_lower = prompt.lower()
    prompt_domains = set()
    # Heuristic: if a domain/subject file name is mentioned in the prompt, prefer it
    for fname in ordered_files:
        domain = fname.replace('.json','').lower()
        if domain in prompt_lower:
            prompt_domains.add(domain)

    for term in terms:
        best_tidbit = None
        best_score = -1
        best_file = None
        for fname in ordered_files:
            entry = file_term_defs.get(fname, {}).get(term)
            if entry:
                candidates = []
                if isinstance(entry, dict):
                    if 'definition' in entry and entry['definition']:
                        candidates.append(entry['definition'])
                    if 'gloss' in entry and entry['gloss']:
                        candidates.append(entry['gloss'])
                elif isinstance(entry, str):
                    candidates.append(entry)
                elif isinstance(entry, list):
                    for e in entry:
                        if isinstance(e, dict):
                            if 'definition' in e and e['definition']:
                                candidates.append(e['definition'])
                            if 'gloss' in e and e['gloss']:
                                candidates.append(e['gloss'])
                        elif isinstance(e, str):
                            candidates.append(e)
                # Score each candidate for contextual/domain relevance
                for cand in candidates:
                    cand_l = cand.lower()
                    score = 0
                    # Strongly prefer if the file's domain is mentioned in the prompt
                    domain = fname.replace('.json','').lower()
                    if domain in prompt_domains:
                        score += 10
                    # Prefer longer, more descriptive definitions
                    score += min(len(cand_l) // 50, 2)
                    # Prefer if any prompt word is in the definition
                    if any(w in cand_l for w in prompt_lower.split()):
                        score += 2
                    # Prefer deeper taxonomy (subject file lower in file_priority list)
                    score += (len(ordered_files) - ordered_files.index(fname))
                    if score > best_score:
                        best_score = score
                        best_tidbit = cand
                        best_file = fname
        if best_tidbit and best_score >= 0:
            token_defs[term] = best_tidbit

    # Handle personal pronoun logic: skip initial pronoun unless subject is referenced later
    personal_pronouns = {
        'i', 'me', 'my', 'mine', 'myself',
        'you', 'your', 'yours', 'yourself', 'yourselves',
        'he', 'him', 'his', 'himself',
        'she', 'her', 'hers', 'herself',
        'it', 'its', 'itself',
        'we', 'us', 'our', 'ours', 'ourselves',
        'they', 'them', 'their', 'theirs', 'themselves',
        'this', 'that', 'these', 'those',
        'who', 'whom', 'whose', 'which', 'what', 'where', 'when', 'why', 'how'
    }
    # If the first token is a personal pronoun, skip it unless it is referenced later in the prompt
    skip_first = False
    if prompt_tokens and prompt_tokens[0].lower() in personal_pronouns:
        skip_first = True
    subject_terms = set(terms)
    referenced_later = any(t.lower() in subject_terms for t in prompt_tokens[1:])

    # --- Compose response with domain lineage and siblings ---
    import random
    affirmatives = [
        "Certainly.", "Of course.", "Here's what I found:", "Affirmative.", "Let me explain:", "Absolutely.", "Here's the information:", "Sure.", "Indeed.", "As requested:", "Here's a summary:", "Let me clarify:", "Here's what the data shows:", "According to the data:", "Based on available information:", "Here's what I know:"
    ]
    response_lines = []
    if skip_first and not referenced_later:
        pass
    else:
        response_lines.append(random.choice(affirmatives))

    affirmations = [
        "Absolutely!", "You got it!", "Here's something cool:", "Let's explore:", "For sure!", "Glad you asked!", "Here's a fun fact:", "Indeed!", "With pleasure!", "Let's dive in!"
    ]
    new_fragments = []
    for t in terms:
        info = domain_info.get(t)
        definition = token_defs.get(t)
        if info:
            sentence = random.choice(affirmations) + " "
            if info['subspecies']:
                noun_taxonomy = f"In the world of {info['kingdom']}, '{info['type']}' (sometimes called {', '.join(info['subspecies'])})"
            else:
                noun_taxonomy = f"In the world of {info['kingdom']}, '{info['type']}'"
            if definition:
                sentence += f"{noun_taxonomy} means {definition.strip('. ')}."
            else:
                sentence += f"{noun_taxonomy} is a fascinating concept!"
            new_fragments.append(sentence)
        elif definition:
            sentence = random.choice(affirmations) + f" {t.capitalize()} means {definition.strip('. ')}."
            new_fragments.append(sentence)

    # Remove from previous_answer any fragments not related to the new prompt's terms
    import re
    def fragment_related_to_terms(fragment, terms):
        for t in terms:
            if re.search(rf"\b{re.escape(t)}\b", fragment, re.IGNORECASE):
                return True
        return False
    prev_fragments = re.split(r'(?<=[.!?])\s+', previous_answer.strip()) if previous_answer else []
    kept_prev = [frag for frag in prev_fragments if fragment_related_to_terms(frag, terms)]
    # Splice in new masterkey'd fragments
    response_lines = kept_prev + new_fragments
    response = ' '.join(response_lines)
    # Store this answer for next turn
    respond_subject_specific._last_answer = response
    return response if response.strip() else "No subject-specific definitions found for your query."
def extract_subject_modifier_pairs(text: str, defs: dict) -> list:
    """
    Extract (subject, modifier) pairs in linear order from the text.
    Subject: noun or noun phrase present in defs.
    Modifier: any sequence of adjectives/descriptive words directly before the subject.
    Returns: list of (full_phrase, subject, modifiers) in order of appearance.
    """
    import re
    tokens = re.findall(r"\b\w+\b", text)
    pairs = []
    used = set()
    n = len(tokens)
    # Try to match the longest possible phrases in defs (up to 4 words)
    i = 0
    while i < n:
        found = False
        for span in (4, 3, 2, 1):
            if i + span > n:
                continue
            phrase_tokens = tokens[i:i+span]
            phrase = ' '.join(phrase_tokens).lower()
            if phrase in defs and phrase not in RELATIONAL_EXCLUSIONS and phrase not in used:
                # Modifiers: all words before the last word in the phrase (including participles/determiners)
                modifiers = phrase_tokens[:-1]
                subject = phrase_tokens[-1]
                full_phrase = ' '.join(phrase_tokens)
                pairs.append((full_phrase, subject, modifiers))
                used.add(phrase)
                found = True
                i += span - 1
                break
        i += 1
    # Always include the main subject (first noun-like phrase in tokens that is in defs), even if preceded by modifiers/participles
    found_main = False
    for span in (4, 3, 2, 1):
        for i in range(n - span + 1):
            phrase_tokens = tokens[i:i+span]
            phrase = ' '.join(phrase_tokens).lower()
            if phrase in defs and phrase not in RELATIONAL_EXCLUSIONS and phrase not in used:
                pairs.insert(0, (' '.join(phrase_tokens), phrase_tokens[-1], phrase_tokens[:-1]))
                found_main = True
                break
        if found_main:
            break
    return pairs


# ===============================
# Natural Language Knowledge Engine
# ===============================
# Modular, maintainable, and robust code/definition engine with context, scoring, and extensibility.

# --- Imports and Global Constants ---

import os
import re
import json
import math
from typing import Any, Dict, List, Optional, Tuple
from new_natural_code_engine import NaturalCodeEngine

# Exclude generic relational words from term extraction and synonym expansion
RELATIONAL_EXCLUSIONS = {
    "part", "type", "kind", "form", "aspect", "element", "component", "piece", "portion", "section", "segment", "member", "item", "thing", "division", "fragment", "bit", "share", "slice", "sample", "example", "instance", "case", "category", "class", "group", "variety", "sort", "genre", "species", "order", "family", "set", "subset", "subgroup", "variation", "modification", "version", "model", "pattern", "style", "manner", "mode", "means", "method", "way", "approach", "system", "structure", "framework", "arrangement", "composition", "configuration", "constitution", "makeup", "fabric", "texture", "substance", "material", "matter", "object", "entity", "unit"
}

SAFE_GLOBALS = {"math": math, "__builtins__": {}}


def score_sentence_against_knowledge(sentence: str, knowledge: dict) -> float:
    """
    Score a sentence for overlap with known knowledge/definitions.
    Inverted scoring: 1 - (unknown words / total words).
    """
    words = [w.strip('.,!?;:').lower() for w in sentence.split() if w.strip('.,!?;:')]
    if not words:
        return 1.0
    known_words = set(
        w
        for info in knowledge.values()
        for definition in info.get('definitions', [])
        for w in definition.lower().split()
    ) | set(
        w
        for info in knowledge.values()
        for _, rel_val in info.get('relations', [])
        for w in str(rel_val).lower().split()
    )
    unknown_count = sum(1 for w in words if w not in known_words)
    score = 1.0 - (unknown_count / len(words))
    return max(0.0, min(1.0, score))

def resolve_pronouns(sentence: str, context: List[str]) -> str:
    """
    Replace third-person pronouns in a sentence with the main subject from recent context.
    """
    pronouns = {"he", "she", "it", "they", "them", "his", "her", "their", "its"}
    tokens = sentence.split()
    referent = None
    if context:
        last = context[-1]
        stopwords = {"the", "a", "an", "of", "to", "in", "for", "on", "with", "at", "by", "from", "up", "about", "into", "over", "after", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"}
        last_tokens = [w for w in last.split() if w.lower() not in stopwords and w.lower() not in pronouns]
        if last_tokens:
            referent = last_tokens[0]
    resolved = [referent if t.lower() in pronouns and referent else t for t in tokens]
    return ' '.join(resolved)
# Convenience function to load the full unified knowledge index
def get_full_knowledge() -> dict:
    """Load and return the full unified knowledge index from all data/*.json files."""
    return load_all_knowledge("data")
def normalize_key(key: str) -> str:
    """Normalize a key for matching: remove interrogatives, underscores, hyphens, and extra spaces."""
    interrogatives = ['what', 'which', 'who', 'whom', 'whose', 'when', 'where', 'why', 'how']
    key = key.replace('_', ' ').replace('-', ' ').lower()
    key = key.replace(' of ', ' ')
    key = ' '.join(key.split())
    words = [w for w in key.split() if w not in interrogatives]
    return ' '.join(words)

def singularize(word: str) -> str:
    """Convert simple English plurals to singular."""
    if word.endswith('ies'):
        return word[:-3] + 'y'
    if word.endswith('es'):
        return word[:-2]
    if word.endswith('s') and not word.endswith('ss'):
        return word[:-1]
    return word

def key_to_word_set(key: str) -> set:
    """Return set of words in key, including singularized forms."""
    words = normalize_key(key).split()
    return set(words + [singularize(w) for w in words])
# eng9.py


import json
import math
import re
from typing import Any, Dict, List, Optional, Tuple

# Import NaturalCodeEngine
from new_natural_code_engine import NaturalCodeEngine

# ---------------------------------------------------------------------
# Safe evaluation context for math expressions and exec lambdas
# ---------------------------------------------------------------------

SAFE_GLOBALS = {
    "math": math,
    "__builtins__": {}
}


# ---------------------------------------------------------------------
# Loading and normalization
# ---------------------------------------------------------------------

import json
import os



def load_all_knowledge(directory: str = "data") -> dict:
    """
    Recursively load all JSON files in the directory and subdirectories.
    Build a unified knowledge index capturing definitions, relationships, formulas, exec, and cross-references.
    Returns: dict of term -> { 'definitions': [...], 'relations': [...], 'formulas': [...], 'exec': [...], 'sources': [...] }
    """
    knowledge = {}
    for root, _, files in os.walk(directory):
        for filename in files:
            if filename.endswith(".json"):
                path = os.path.join(root, filename)
                with open(path, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except Exception as e:
                        print(f"Error loading {path}: {e}")
                        continue
                    if isinstance(data, dict):
                        for k, v in data.items():
                            entry = knowledge.setdefault(k, {'definitions': [], 'relations': [], 'formulas': [], 'exec': [], 'sources': set()})
                            # Definitions
                            if isinstance(v, str):
                                entry['definitions'].append(v)
                            elif isinstance(v, dict):
                                if 'definition' in v:
                                    entry['definitions'].append(v['definition'])
                                if 'gloss' in v:
                                    entry['definitions'].append(v['gloss'])
                                # Relations
                                for rel_key in ['is a', 'type of', 'class of', 'category of', 'related to', 'see also', 'synonyms']:
                                    if rel_key in v:
                                        rels = v[rel_key]
                                        if isinstance(rels, str):
                                            entry['relations'].append((rel_key, rels))
                                        elif isinstance(rels, list):
                                            for rel in rels:
                                                entry['relations'].append((rel_key, rel))
                                # Formulas
                                if 'formula' in v:
                                    entry['formulas'].append(v['formula'])
                                # Executable code
                                if 'exec' in v:
                                    entry['exec'].append(v['exec'])
                            elif isinstance(v, list):
                                for item in v:
                                    if isinstance(item, dict):
                                        if 'definition' in item:
                                            entry['definitions'].append(item['definition'])
                                        if 'gloss' in item:
                                            entry['definitions'].append(item['gloss'])
                                        for rel_key in ['is a', 'type of', 'class of', 'category of', 'related to', 'see also', 'synonyms']:
                                            if rel_key in item:
                                                rels = item[rel_key]
                                                if isinstance(rels, str):
                                                    entry['relations'].append((rel_key, rels))
                                                elif isinstance(rels, list):
                                                    for rel in rels:
                                                        entry['relations'].append((rel_key, rel))
                                        if 'formula' in item:
                                            entry['formulas'].append(item['formula'])
                                        if 'exec' in item:
                                            entry['exec'].append(item['exec'])
                            entry['sources'].add(filename)
                    elif isinstance(data, list):
                        base_name = os.path.splitext(os.path.basename(path))[0]
                        entry = knowledge.setdefault(base_name, {'definitions': [], 'relations': [], 'formulas': [], 'exec': [], 'sources': set()})
                        for item in data:
                            if isinstance(item, dict):
                                if 'definition' in item:
                                    entry['definitions'].append(item['definition'])
                                if 'gloss' in item:
                                    entry['definitions'].append(item['gloss'])
                                for rel_key in ['is a', 'type of', 'class of', 'category of', 'related to', 'see also', 'synonyms']:
                                    if rel_key in item:
                                        rels = item[rel_key]
                                        if isinstance(rels, str):
                                            entry['relations'].append((rel_key, rels))
                                        elif isinstance(rels, list):
                                            for rel in rels:
                                                entry['relations'].append((rel_key, rel))
                                if 'formula' in item:
                                    entry['formulas'].append(item['formula'])
                                if 'exec' in item:
                                    entry['exec'].append(item['exec'])
                        entry['sources'].add(filename)
                    else:
                        print(f"Warning: {path} is not a dict or list. Skipping.")
    # Convert sources to list for serialization
    for v in knowledge.values():
        v['sources'] = list(v['sources'])
    return knowledge

def normalize_defs(defs: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Normalize all entries so they become:
    term: [ { gloss: "...", formula: ..., exec: ... } ]
    """
    normalized = {}

    for term, entry in defs.items():

        # Case 1: entry is a string → treat as gloss
        if isinstance(entry, str):
            normalized[term] = [
                {
                    "gloss": entry
                }
            ]
            continue

        # Case 2: entry is a dict → wrap in list
        if isinstance(entry, dict):
            normalized[term] = [entry]
            continue

        # Case 3: entry is a list → ensure each element is a dict
        if isinstance(entry, list):
            fixed_list = []
            for item in entry:
                if isinstance(item, str):
                    fixed_list.append({"gloss": item})
                elif isinstance(item, dict):
                    fixed_list.append(item)
            normalized[term] = fixed_list
            continue

        # Fallback: ignore weird types
        normalized[term] = []

    return normalized

def load_all_definitions() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load core definitions and math definitions,
    merge them into a single normalized dictionary.
    """
    # Use the new unified loader, but extract only definitions for legacy compatibility
    knowledge = load_all_knowledge("data")
    defs = {}
    for term, info in knowledge.items():
        # Prefer structured definitions
        if info['definitions']:
            defs[term] = [{"gloss": d} for d in info['definitions']]
    return normalize_defs(defs)


# ---------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------


import ast
import operator as op

def try_eval_expression(text: str, variables: dict = None) -> Optional[float]:
    """
    Evaluate a math expression with variables and correct order of operations.
    Supports: +, -, *, /, **, %, parentheses, and variables.
    Example: '2*x + 3*y', variables={'x': 4, 'y': 5}
    """
    if not text or not isinstance(text, str):
        return None
    expr = text.strip().replace('^', '**')
    variables = variables or {}
    # Supported operators
    allowed_operators = {
        ast.Add: op.add,
        ast.Sub: op.sub,
        ast.Mult: op.mul,
        ast.Div: op.truediv,
        ast.Pow: op.pow,
        ast.Mod: op.mod,
        ast.USub: op.neg,
        ast.UAdd: op.pos
    }
    def eval_node(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            return allowed_operators[type(node.op)](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = eval_node(node.operand)
            return allowed_operators[type(node.op)](operand)
        elif isinstance(node, ast.Name):
            if node.id in variables:
                return variables[node.id]
            else:
                raise ValueError(f"Unknown variable: {node.id}")
        else:
            raise TypeError(f"Unsupported expression: {ast.dump(node)}")
    try:
        parsed = ast.parse(expr, mode='eval')
        return eval_node(parsed.body)
    except Exception:
        return None


def parse_math_exec(defs: Dict[str, List[Dict[str, Any]]], term: str, *args: float) -> Optional[Any]:
    """
    Execute the math function stored in the 'exec' field of a definition.
    Returns the result on success, or None on error or if not executable.
    """
    entry = defs.get(term)
    if not entry:
        return None

    sense = entry[0]
    if isinstance(sense, dict):
        code = sense.get("exec")
    else:
        code = None
    if not code:
        return None

    try:
        fn = eval(code, SAFE_GLOBALS, {})
    except Exception:
        return None

    try:
        return fn(*args)
    except Exception:
        return None


# ---------------------------------------------------------------------
# Operator precedence helpers
# ---------------------------------------------------------------------
def get_operator_precedence(op: str) -> int:
    """
    Return precedence level for a given operator string.
    Higher number = higher precedence.
    """
    precedence = {
        '**': 4,
        '^': 4,
        '*': 3,
        '/': 3,
        '//': 3,
        '%': 3,
        '+': 2,
        '-': 2,
    }
    return precedence.get(op, 0)


# ---------------------------------------------------------------------
# Sense selection and definition building
# ---------------------------------------------------------------------

def choose_sense(senses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Choose a single sense from a list.
    For now, select the first sense.
    """
    if not senses or not isinstance(senses, list) or len(senses) == 0:
        return {}
    return senses[0]


def build_definition_style(term: str, core_phrase: str, detail_phrases: List[str], formula: Optional[str] = None) -> str:
    """
    Build a clean academic definition sentence, optionally including a formula.
    Example:
    "addition is the process of combining quantities to produce a total.
     The formula is a + b."
    """
    core_phrase = core_phrase.strip()
    if not core_phrase:
        # print("[DEBUG] Fallback: core_phrase is empty, using 'a mathematical concept'.")
        core_phrase = "a mathematical concept"

    # Simple article handling: a / an / the
    if not re.match(r"\b(a|an|the)\b ", core_phrase):
        if core_phrase[0].lower() in "aeiou":
            core_phrase = "an " + core_phrase
        else:
            core_phrase = "a " + core_phrase

    detail_phrases = [d.strip() for d in detail_phrases if d.strip()]

    if detail_phrases:
        if len(detail_phrases) == 1:
            tail = detail_phrases[0]
        else:
            tail = ", ".join(detail_phrases[:-1]) + ", and " + detail_phrases[-1]
        base = f"{term} is {core_phrase} that {tail}."
    else:
        base = f"{term} is {core_phrase}."

    if formula:
        base += f" The formula is {formula}."

    return base


def split_gloss(gloss: str) -> Tuple[str, List[str]]:
    """
    Split a gloss into a core phrase and detail phrases.
    The first clause becomes the core; the rest become details.
    """
    text = gloss.strip()
    if not text:
        return "a mathematical concept", []

    # Split on basic separators: semicolons or periods
    parts = re.split(r"[;\.]", text)
    parts = [p.strip() for p in parts if p.strip()]

    if not parts:
        return text, []

    # Brute-force: combine parts until a full sentence or closed quote is detected
    core = parts[0]
    quote_chars = ['"', "'", "“", "”"]
    def count_quotes(s, q):
        return s.count(q)
    def is_quote_open(s):
        for q in quote_chars:
            if count_quotes(s, q) % 2 == 1:
                return q
        return None

    i = 1
    while i < len(parts):
        open_q = is_quote_open(core)
        # If in a quote, keep adding until quote is closed
        if open_q:
            core += '. ' + parts[i]
            i += 1
            continue
        # If not in a quote, check for sentence-ending punctuation
        if core and core[-1] in '.!?':
            break
        # If next part starts with a lowercase letter, likely a continuation
        if parts[i] and parts[i][0].islower():
            core += '. ' + parts[i]
            i += 1
            continue
        # Otherwise, treat as end of core
        break
    details = parts[i:]
    return core, details


# ---------------------------------------------------------------------
# Main respond function
# ---------------------------------------------------------------------



# --- Relational exclusions (generic words and synonyms) ---
relational_exclusions = {"part", "type", "kind", "form", "aspect", "element", "component", "piece", "portion", "section", "segment", "member", "item", "thing", "division", "fragment", "bit", "share", "slice", "sample", "example", "instance", "case", "category", "class", "group", "variety", "sort", "genre", "species", "order", "family", "set", "subset", "subgroup", "variation", "modification", "version", "model", "pattern", "style", "manner", "mode", "means", "method", "way", "approach", "system", "structure", "framework", "arrangement", "composition", "configuration", "constitution", "makeup", "fabric", "texture", "substance", "material", "matter", "object", "entity", "unit"}

import string
import re

def extract_master_key(raw: str) -> Optional[str]:
    """Extract explicit master key from prompt (e.g. 'what is X', 'what does X mean')."""
    m = re.match(r"what is ([\w\-\_ ]+)[\?\.]?", raw.lower())
    if m:
        return m.group(1).strip()
    m = re.match(r"what does ([\w\-\_ ]+) mean[\?\.]?", raw.lower())
    if m:
        return m.group(1).strip()
    return None

def strip_punct(word: str) -> str:
    return word.rstrip(string.punctuation)

def extract_terms(text: str) -> List[str]:
    """Extract all relevant terms from prompt, using stopword and verb filtering."""
    import re
    # Split on non-word boundaries to handle punctuation and concatenated forms
    tokens = re.findall(r"\b\w+\b", text)
    lower_tokens = [t.lower() for t in tokens]
    interrogatives = {'what','which','who','whom','whose','when','where','why','how','is','are','was','were','do','does','did','can','could','will','would','should','has','have','had'}
    affirmation_words = {'right', 'yes', 'yeah', 'yep', 'true', 'okay', 'ok', 'sure', 'certainly', 'absolutely', 'indeed', 'definitely', 'affirmative', 'correct'}
    common_verbs = {'is','are','was','were','do','does','did','can','could','will','would','should','has','have','had','be','am','being','been','get','got','gets','make','makes','made','go','goes','went','gone','see','seen','say','says','said','know','knows','knew','think','thinks','thought','want','wants','wanted','need','needs','needed','use','uses','used','like','likes','liked','give','gives','gave','find','finds','found','tell','tells','told','work','works','worked','call','calls','called','try','tries','tried','ask','asks','asked','feel','feels','felt','leave','leaves','left','put','puts','keep','keeps','kept','let','lets','begin','begins','began','begun','seem','seems','seemed','help','helps','helped','talk','talks','talked','turn','turns','turned','start','starts','started','show','shows','showed','hear','hears','heard','play','plays','played','run','runs','ran','move','moves','moved','live','lives','lived','believe','believes','believed','bring','brings','brought','happen','happens','happened','write','writes','wrote','written','provide','provides','provided','sit','sits','sat','stand','stands','stood','lose','loses','lost','pay','pays','paid','meet','meets','met','include','includes','included','continue','continues','continued','set','sets','learn','learns','learned','change','changes','changed','lead','leads','led','understand','understands','understood','watch','watches','watched','follow','follows','followed','stop','stops','stopped','create','creates','created','speak','speaks','spoke','spoken','read','reads','read','allow','allows','allowed','add','adds','added','spend','spends','spent','grow','grows','grew','grown','open','opens','opened','walk','walks','walked','win','wins','won','offer','offers','offered','remember','remembers','remembered','love','loves','loved','consider','considers','considered','appear','appears','appeared','buy','buys','bought','wait','waits','waited','serve','serves','served','die','dies','died','send','sends','sent','expect','expects','expected','build','builds','built','stay','stays','stayed','fall','falls','fell','fallen','cut','cuts','cut','reach','reaches','reached','kill','kills','killed','remain','remains','remained'}
    stopwords = interrogatives | affirmation_words | common_verbs | {"the","a","an","of","to","in","for","on","with","at","by","from","up","about","into","over","after","under","again","further","then","once","here","there","when","where","why","how","all","any","both","each","few","more","most","other","some","such","no","nor","not","only","own","same","so","than","too","very","s","t","can","will","just","don","should","now"}
    # List of personal pronouns to skip
    personal_pronouns = {
        'i', 'me', 'my', 'mine', 'myself',
        'you', 'your', 'yours', 'yourself', 'yourselves',
        'he', 'him', 'his', 'himself',
        'she', 'her', 'hers', 'herself',
        'it', 'its', 'itself',
        'we', 'us', 'our', 'ours', 'ourselves',
        'they', 'them', 'their', 'theirs', 'themselves',
        'this', 'that', 'these', 'those',
        'who', 'whom', 'whose', 'which', 'what', 'where', 'when', 'why', 'how'
    }
    seen = set()
    original_tokens = text.split()
    # Heuristic: treat capitalized or non-stopword/verb as noun, but skip personal pronouns
    candidate_terms = []
    for orig, low in zip(tokens, lower_tokens):
        if (orig[0].isupper() or (low not in stopwords and low.isalpha())) and low not in RELATIONAL_EXCLUSIONS and low not in personal_pronouns:
            norm = strip_punct(singularize(orig))
            if norm and norm not in seen:
                seen.add(norm)
                candidate_terms.append(norm)
    terms = candidate_terms
    # If no terms remain, allow a relational word as fallback
    if not terms:
        for orig, low in zip(original_tokens, lower_tokens):
            norm = strip_punct(singularize(orig))
            if norm and norm not in seen:
                terms.append(norm)
                break
    if not terms:
        # fallback: treat the whole phrase as a single term
        phrase = strip_punct(text.strip())
        if phrase:
            terms = [phrase]
    return terms

def lookup_definition(defs: Dict[str, Any], term: str) -> Optional[Any]:
    """Find the best-matching definition entry for a term (normalized)."""
    norm_term = normalize_key(term)
    for k in defs:
        norm_k = normalize_key(k)
        if norm_k == norm_term:
            return defs[k]
    return None


def respond(defs: Dict[str, List[Dict[str, Any]]], text: str) -> str:

    raw = text.strip()
    if not raw:
        return "I need something to define."

    # Context and pronoun resolution
    if not hasattr(respond, "_context"):
        respond._context = []
    context = respond._context
    resolved_raw = resolve_pronouns(raw, context)
    context.append(raw)
    if len(context) > 10:
        context.pop(0)

    # Extract subject(s)
    master_key = extract_master_key(resolved_raw)
    if master_key:
        terms = [strip_punct(master_key)]
    else:
        terms = extract_terms(resolved_raw)

    subj_mod_pairs = extract_subject_modifier_pairs(resolved_raw, defs)
    def build_fluent_subject(filtered_pairs):
        phrases = [fp for fp, _, _ in filtered_pairs]
        if not phrases:
            return ''
        if len(phrases) == 1:
            return phrases[0]
        if len(phrases) == 2:
            return f"{phrases[0]} and {phrases[1]}"
        return f"{', '.join(phrases[:-1])}, and {phrases[-1]}"

    if subj_mod_pairs:
        seen_subjects = set()
        filtered_pairs = []
        for full_phrase, subj, modifiers in subj_mod_pairs:
            key = (full_phrase.lower(), subj.lower())
            if key not in seen_subjects:
                filtered_pairs.append((full_phrase, subj, modifiers))
                seen_subjects.add(key)
        subject_phrase = build_fluent_subject(filtered_pairs)
        if subject_phrase:
            subjects = [subject_phrase]
        else:
            subjects = [t for t in terms if t.lower() not in RELATIONAL_EXCLUSIONS]
    else:
        subjects = [t for t in terms if t.lower() not in RELATIONAL_EXCLUSIONS]

    # --- Subject mirror and braided crescendo outward ---
    # Improve subject extraction: prefer noun phrases, filter out auxiliary verbs
    import random
    # Define stopwords in this scope so is_noun can access it
    verbs = {"is", "are", "was", "were", "be", "am", "being", "been", "do", "does", "did", "can", "could", "will", "would", "should", "has", "have", "had"}
    generic = {"that", "which", "process", "chemical", "reactions", "about", "wrong"}
    stopwords = {'what','which','who','whom','whose','when','where','why','how','is','are','was','were','do','does','did','can','could','will','would','should','has','have','had','be','am','being','been','get','got','gets','make','makes','made','go','goes','went','gone','see','seen','say','says','said','know','knows','knew','think','thinks','thought','want','wants','wanted','need','needs','needed','use','uses','used','like','likes','liked','give','gives','gave','find','finds','found','tell','tells','told','work','works','worked','call','calls','called','try','tries','tried','ask','asks','asked','feel','feels','felt','leave','leaves','left','put','puts','keep','keeps','kept','let','lets','begin','begins','began','begun','seem','seems','seemed','help','helps','helped','talk','talks','talked','turn','turns','turned','start','starts','started','show','shows','showed','hear','hears','heard','play','plays','played','run','runs','ran','move','moves','moved','live','lives','lived','believe','believes','believed','bring','brings','brought','happen','happens','happened','write','writes','wrote','written','provide','provides','provided','sit','sits','sat','stand','stands','stood','lose','loses','lost','pay','pays','paid','meet','meets','met','include','includes','included','continue','continues','continued','set','sets','learn','learns','learned','change','changes','changed','lead','leads','led','understand','understands','understood','watch','watches','watched','follow','follows','followed','stop','stops','stopped','create','creates','created','speak','speaks','spoke','spoken','read','reads','read','allow','allows','allowed','add','adds','added','spend','spends','spent','grow','grows','grew','grown','open','opens','opened','walk','walks','walked','win','wins','won','offer','offers','offered','remember','remembers','remembered','love','loves','loved','consider','considers','considered','appear','appears','appeared','buy','buys','bought','wait','waits','waited','serve','serves','served','die','dies','died','send','sends','sent','expect','expects','expected','build','builds','built','stay','stays','stayed','fall','falls','fell','fallen','cut','cuts','cut','reach','reaches','reached','kill','kills','killed','remain','remains','remained',"the","a","an","of","to","in","for","on","with","at","by","from","up","about","into","over","after","under","again","further","then","once","here","there","when","where","why","how","all","any","both","each","few","more","most","other","some","such","no","nor","not","only","own","same","so","than","too","very","s","t","can","will","just","don","should","now"}
    def is_noun(word):
        # Simple heuristic: not a verb, not a stopword, not a generic word
        return word.lower() not in verbs and word.lower() not in generic and word.lower() not in stopwords
    subject_words = [w for w in ' '.join(subjects).split() if is_noun(w)]
    subject_str = ' '.join(subject_words) if subject_words else ', '.join(subjects)
    # More varied and context-aware auxiliary phrasing
    aux_phrases = [
        f"Considering {subject_str}, we encounter a spectrum of associations.",
        f"The topic of {subject_str} opens the door to a rich landscape of ideas.",
        f"In the world of {subject_str}, many threads of meaning are woven together.",
        f"Reflecting on {subject_str}, we find it linked to a variety of qualities and phenomena.",
        f"{subject_str.capitalize()} stands at the intersection of multiple domains and concepts."
    ]
    response = random.choice(aux_phrases)

    # Braided crescendo: find most salient, high-frequency, or contextually associated concepts in all definitions
    from collections import Counter, defaultdict
    word_counter = Counter()
    word_to_terms = defaultdict(set)
    for term, senses in defs.items():
        for sense in senses:
            gloss = sense.get("gloss", "")
            for w in re.findall(r"\b\w+\b", gloss.lower()):
                word_counter[w] += 1
                word_to_terms[w].add(term)

    # Filter out generic/filler words from salient associations
    filler = {"that", "which", "process", "chemical", "reactions", "about", "wrong", "pathways"}
    filtered_words = [w for w, _ in word_counter.most_common(200) if w not in stopwords and w not in subject_words and w not in filler and len(w) > 2]

    associated_words = Counter()
    for w in filtered_words:
        for term in word_to_terms[w]:
            for s in defs[term]:
                gloss = s.get("gloss", "").lower()
                if any(sw in gloss for sw in subject_words):
                    associated_words[w] += 1

    # Favor domain-relevant associations for common subjects
    domain_map = {
        "guitar": ["music", "instrument", "sound", "strings", "weight", "play", "tone"],
        "marijuana": ["substance", "effect", "legal", "medical", "use", "plant", "psychoactive"],
        "heroin": ["drug", "addiction", "opioid", "effect", "risk", "medical", "illegal"],
        "cocaine": ["stimulant", "drug", "effect", "risk", "medical", "illegal"],
        "football": ["sport", "ball", "team", "game", "field", "score", "play"],
        "basketball": ["sport", "ball", "team", "game", "court", "score", "play"]
    }
    N = 5
    salient_words = []
    for key, domain_words in domain_map.items():
        if key in subject_str.lower():
            # Prefer domain words if present in associations
            salient_words = [w for w in domain_words if w in associated_words or w in filtered_words][:N]
            break
    if not salient_words:
        if associated_words:
            salient_words = [w for w, _ in associated_words.most_common(N)]
        else:
            salient_words = filtered_words[:N]

    if salient_words:
        salient_list = ', '.join(salient_words)
        braid_phrases = [
            f"Among its many facets, {subject_str} is closely braided with concepts such as {salient_list}.",
            f"The resonance of {subject_str} is amplified by its association with {salient_list}.",
            f"One finds {subject_str} frequently braided together with {salient_list} in discourse and analysis.",
            f"The interplay between {subject_str} and {salient_list} enriches its meaning and relevance.",
            f"In the grand weave of ideas, {subject_str} and {salient_list} are often found side by side."
        ]
        response += " " + random.choice(braid_phrases)
        response += f" This highlights a dimension of awareness and association in relation to {subject_str}."
    else:
        response += f" {subject_str} is a concept with many dimensions and associations, depending on context."

    return response


# ---------------------------------------------------------------------
# Simple CLI loop for manual testing
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Simple CLI loop for manual testing
# ---------------------------------------------------------------------

def test_blend_fragments():
    """Test and print the last sentence fragments used in blending."""
    if hasattr(blend_definitions, '_last_fragments'):
        print("Fragments used in last blend:")
        for i, frag in enumerate(blend_definitions._last_fragments, 1):
            print(f"Fragment {i}: {frag}")
    else:
        print("No fragments stored yet.")


# ---------------------------------------------------------------------
# Taxonomic grammar demo helper
# ---------------------------------------------------------------------
try:
    from taxonomic_grammar import analyze as _tg_analyze, render_response as _tg_render, generate_variations as _tg_variations
except Exception:
    _tg_analyze = None
    _tg_render = None
    _tg_variations = None
try:
    from nerve_center import nerve as _nerve
except Exception:
    _nerve = None

def taxonomy_demo(prompt=None, variations_steps=0):
    """Run taxonomic analysis on `prompt`. If `prompt` is None, read from stdin.

    If `variations_steps` > 0 and the variation generator is available, also print
    a sequence of alternative rendered summaries that traverse genus (`variable`) via a sine wave.
    """
    if _tg_analyze is None:
        print("taxonomic_grammar module not available")
        return None
    if prompt is None:
        prompt = input('Enter prompt for taxonomy analysis: ')
    import json
    out = _tg_analyze(prompt)
    # Print structured JSON and a friendly rendered response if available
    print(json.dumps(out, indent=2, ensure_ascii=False))
    if _tg_render:
        print('\n--- Friendly taxonomy summary ---')
        print(_tg_render(out, max_items=6, positivity=True))

    if variations_steps and _tg_variations:
        print('\n--- Variations (sine-wave genus traversal) ---')
        variations = _tg_variations(out, steps=variations_steps, positivity=True)
        for v in variations:
            print('\n' + v)

    return out


def nerve_demo(prompt=None, variations_steps=0, top_n=5):
    """Create a nerve session from a prompt and show top items.

    - Runs taxonomy analysis (prints structured JSON and friendly summary).
    - Creates a persisted session in `data/nerve_sessions` via `nerve_center.NerveCenter`.
    - Prints top `top_n` items and expands the first variable found.
    Returns the session id (or None).
    """
    if _tg_analyze is None:
        print('taxonomic_grammar module not available')
        return None
    if prompt is None:
        prompt = input('Enter prompt for nerve demo: ')

    # Run taxonomy demo (it prints JSON + summary)
    result = taxonomy_demo(prompt, variations_steps=variations_steps)
    if result is None:
        return None

    if _nerve is None:
        print('nerve_center not available')
        return None

    sid = _nerve.create_session(result)
    print(f'Created nerve session: {sid}')

    tops = _nerve.get_top_items(sid, n=top_n)
    print('\nTop items:')
    import json
    print(json.dumps(tops, indent=2, ensure_ascii=False))

    if tops:
        first_var = tops[0].get('variable')
        if first_var:
            print('\nExpanding first variable:\n')
            print(_nerve.expand_variable(sid, first_var))

    print('\nUse nerve_center.nerve to inspect or load sessions programmatically.')
    return sid

