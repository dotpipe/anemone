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

def try_eval_expression(text: str) -> Optional[float]:
    """
    Try to evaluate a simple numeric expression like:
    1+1, 2*3, (5+5)/2, 3^2

    Allowed characters: digits, decimal point, + - * / ^ ( ) and spaces.
    """
    expr = text.strip()
    if not expr:
        return None

    if not re.fullmatch(r"[0-9\.\+\-\*/\^\(\) ]+", expr):
        return None

    expr = expr.replace("^", "**")
    try:
        value = eval(expr, SAFE_GLOBALS, {})
    except Exception:
        return None
    return value


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
    tokens = text.split()
    lower_tokens = [t.lower() for t in tokens]
    interrogatives = {'what','which','who','whom','whose','when','where','why','how','is','are','was','were','do','does','did','can','could','will','would','should','has','have','had'}
    affirmation_words = {'right', 'yes', 'yeah', 'yep', 'true', 'okay', 'ok', 'sure', 'certainly', 'absolutely', 'indeed', 'definitely', 'affirmative', 'correct'}
    common_verbs = {'is','are','was','were','do','does','did','can','could','will','would','should','has','have','had','be','am','being','been','get','got','gets','make','makes','made','go','goes','went','gone','see','seen','say','says','said','know','knows','knew','think','thinks','thought','want','wants','wanted','need','needs','needed','use','uses','used','like','likes','liked','give','gives','gave','find','finds','found','tell','tells','told','work','works','worked','call','calls','called','try','tries','tried','ask','asks','asked','feel','feels','felt','leave','leaves','left','put','puts','keep','keeps','kept','let','lets','begin','begins','began','begun','seem','seems','seemed','help','helps','helped','talk','talks','talked','turn','turns','turned','start','starts','started','show','shows','showed','hear','hears','heard','play','plays','played','run','runs','ran','move','moves','moved','live','lives','lived','believe','believes','believed','bring','brings','brought','happen','happens','happened','write','writes','wrote','written','provide','provides','provided','sit','sits','sat','stand','stands','stood','lose','loses','lost','pay','pays','paid','meet','meets','met','include','includes','included','continue','continues','continued','set','sets','learn','learns','learned','change','changes','changed','lead','leads','led','understand','understands','understood','watch','watches','watched','follow','follows','followed','stop','stops','stopped','create','creates','created','speak','speaks','spoke','spoken','read','reads','read','allow','allows','allowed','add','adds','added','spend','spends','spent','grow','grows','grew','grown','open','opens','opened','walk','walks','walked','win','wins','won','offer','offers','offered','remember','remembers','remembered','love','loves','loved','consider','considers','considered','appear','appears','appeared','buy','buys','bought','wait','waits','waited','serve','serves','served','die','dies','died','send','sends','sent','expect','expects','expected','build','builds','built','stay','stays','stayed','fall','falls','fell','fallen','cut','cuts','cut','reach','reaches','reached','kill','kills','killed','remain','remains','remained'}
    stopwords = interrogatives | affirmation_words | common_verbs | {"the","a","an","of","to","in","for","on","with","at","by","from","up","about","into","over","after","under","again","further","then","once","here","there","when","where","why","how","all","any","both","each","few","more","most","other","some","such","no","nor","not","only","own","same","so","than","too","very","s","t","can","will","just","don","should","now"}
    # Only extract capitalized or noun-like words (not in stopwords/verbs), unless whole phrase is being asked about
    seen = set()
    original_tokens = text.split()
    # Heuristic: treat capitalized or non-stopword/verb as noun
    candidate_terms = []
    for orig, low in zip(original_tokens, lower_tokens):
        if (orig[0].isupper() or (low not in stopwords and low.isalpha())) and low not in RELATIONAL_EXCLUSIONS:
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

    # --- Subject mirror and crescendo outward ---
    # 1. Mirror the subject
    subject_str = ', '.join(subjects)
    response = f"{subject_str.capitalize()}"

    # 2. Crescendo outward: find most salient, high-frequency, or contextually associated concepts in all definitions
    from collections import Counter, defaultdict
    word_counter = Counter()
    word_to_terms = defaultdict(set)
    for term, senses in defs.items():
        for sense in senses:
            gloss = sense.get("gloss", "")
            for w in re.findall(r"\b\w+\b", gloss.lower()):
                word_counter[w] += 1
                word_to_terms[w].add(term)

    # Remove stopwords and the subject itself from consideration
    stopwords = {"the","a","an","of","to","in","for","on","with","at","by","from","up","about","into","over","after","under","again","further","then","once","here","there","when","where","why","how","all","any","both","each","few","more","most","other","some","such","no","nor","not","only","own","same","so","than","too","very","s","t","can","will","just","don","should","now"}
    subject_words = set(subject_str.lower().split())
    filtered_words = [w for w, _ in word_counter.most_common(200) if w not in stopwords and w not in subject_words and len(w) > 2]

    # Find words that co-occur with the subject in glosses
    associated_words = Counter()
    for w in filtered_words:
        for term in word_to_terms[w]:
            for s in defs[term]:
                gloss = s.get("gloss", "").lower()
                if any(sw in gloss for sw in subject_words):
                    associated_words[w] += 1

    # Take the top N associated words, or fallback to top frequency
    N = 5
    if associated_words:
        salient_words = [w for w, _ in associated_words.most_common(N)]
    else:
        salient_words = filtered_words[:N]

    if salient_words:
        salient_list = ', '.join(salient_words)
        response += f" is closely associated with concepts such as {salient_list}. "
        response += f"This highlights a dimension of awareness and association in relation to {subject_str}."
    else:
        response += f" is a concept with many dimensions and associations, depending on context."

    return response


# ---------------------------------------------------------------------
# Simple CLI loop for manual testing
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Simple CLI loop for manual testing
# ---------------------------------------------------------------------


if __name__ == "__main__":
    definitions = load_all_definitions()
    code_engine = NaturalCodeEngine('data')

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not line:
            continue

        if line.lower() in {"quit", "exit"}:
            break

        # If the prompt looks like a code generation request, use the code engine
        if any(word in line.lower() for word in ["code", "generate", "python", "loop", "function", "print", "if", "while", "for", "define", "create"]):
            code = code_engine.generate_code(line)
            print(code)
        else:
            print(respond(definitions, line))
