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


def load_definitions(directory="data"):
    """
    Recursively load all JSON files in the directory and subdirectories.
    Merge all definitions into a single dictionary, regardless of domain.
    If a file contains a 'domain' key, its definitions are still merged.
    """
    defs = {}
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
                    # Unify all files to the definitions.json structure: { term: [definitions...] }
                    if isinstance(data, dict):
                        for k, v in data.items():
                            defs[k] = v
                    elif isinstance(data, list):
                        # If the file is a list, treat each item as a definition for the file's base name
                        base_name = os.path.splitext(os.path.basename(path))[0]
                        defs[base_name] = data
                    else:
                        print(f"Warning: {path} is not a dict or list. Skipping.")
    return defs

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
    base = load_definitions("definitions.json")
    try:
        mathdefs = load_definitions("math.json")
    except FileNotFoundError:
        mathdefs = {}

    merged: Dict[str, Any] = {**base, **mathdefs}
    return normalize_defs(merged)


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


def parse_math_exec(defs: Dict[str, List[Dict[str, Any]]],
                    term: str,
                    *args: float) -> Optional[Any]:
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
    if not senses:
        return {}
    return senses[0]


def build_definition_style(
    term: str,
    core_phrase: str,
    detail_phrases: List[str],
    formula: Optional[str] = None
) -> str:
    """
    Build a clean academic definition sentence, optionally including a formula.
    Example:
    "addition is the process of combining quantities to produce a total.
     The formula is a + b."
    """
    core_phrase = core_phrase.strip()
    if not core_phrase:
        print("[DEBUG] Fallback: core_phrase is empty, using 'a mathematical concept'.")
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

    core = parts[0]
    details = parts[1:]
    return core, details


# ---------------------------------------------------------------------
# Main respond function
# ---------------------------------------------------------------------

def respond(defs: Dict[str, List[Dict[str, Any]]], text: str) -> str:
    """
    Main response function.
    Priority:
    1. Assignment-style expression: "1+1=x"
    2. Pure expression: "1+1"
    3. Term + arguments with math exec: "addition 3 5"
    4. Term definition: "addition"
    5. Fallback message.
    """
    raw = text.strip()
    if not raw:
        return "I need something to define."

    # -------------------------------------------------------------
    # 1. Assignment-style expression: "1+1=x"
    # -------------------------------------------------------------
    if "=" in raw and not re.search(r"[a-zA-Z]", raw.split("=", 1)[0]):
        left, right = raw.split("=", 1)
        left = left.strip()
        right = right.strip()
        value = try_eval_expression(left)
        if value is not None and right:
            return f"{right} = {value}"

    # -------------------------------------------------------------
    # 2. Pure expression: "1+1", "2*3", "(5+5)/2"
    # -------------------------------------------------------------
    import re
    if not re.search(r"[a-zA-Z]", raw):
        value = try_eval_expression(raw)
        if value is not None:
            return f"{raw} = {value}"

    # -------------------------------------------------------------
    # 3. Tokenize and look for a term in definitions
    # -------------------------------------------------------------
    tokens = raw.split()
    if not tokens:
        return "I need something to define."

    lower_tokens = [t.lower() for t in tokens]

    # Try full normalized prompt as term first
    full_prompt_norm = normalize_key(' '.join(tokens))
    term = lower_tokens[0]
    entry = None
    if full_prompt_norm in [normalize_key(k) for k in defs]:
        for k in defs:
            if normalize_key(k) == full_prompt_norm:
                entry = defs[k]
                print(f"[DEBUG] Direct match for full prompt: '{full_prompt_norm}' == '{k}'")
                break
    # If not, fall back to first token as term
    if not entry:
        term = lower_tokens[0]


    def normalize_key(key):
        # Remove interrogatives, underscores, hyphens, 'of', and collapse spaces
        interrogatives = ['what', 'which', 'who', 'whom', 'whose', 'when', 'where', 'why', 'how']
        key = key.replace('_', ' ').replace('-', ' ').lower()
        key = key.replace(' of ', ' ')
        key = ' '.join(key.split())
        words = [w for w in key.split() if w not in interrogatives]
        return ' '.join(words)


    def singularize(word):
        # Simple English plural to singular
        if word.endswith('ies'):
            return word[:-3] + 'y'
        if word.endswith('es'):
            return word[:-2]
        if word.endswith('s') and not word.endswith('ss'):
            return word[:-1]
        return word

    def key_to_word_set(key):
        # Include both original and singularized forms
        words = normalize_key(key).split()
        return set(words + [singularize(w) for w in words])

    # Try direct match
    entry = defs.get(term)
    if entry:
        print(f"[DEBUG] Direct match for term: '{term}'")

    # Extra debug: show all keys that contain all prompt words (after normalization)
    prompt_words_full = [singularize(w) for w in normalize_key(' '.join(tokens)).split()]
    matching_keys = []
    for k in defs:
        k_norm = normalize_key(k)
        if all(w in k_norm.split() for w in prompt_words_full):
            matching_keys.append(k)
    if matching_keys:
        print(f"[DEBUG] Keys containing all prompt words: {matching_keys}")
    # Try underscore-to-space, fuzzy, and regex/word matches
    if not entry:
        term_set = key_to_word_set(term)
        for k in defs:
            k_set = key_to_word_set(k)
            overlap = len(term_set & k_set)
            max_len = max(len(term_set), len(k_set))
            if max_len > 0 and overlap / max_len >= 0.8:
                print(f"[DEBUG] Fuzzy word overlap match: '{term}' ~ '{k}' (overlap {overlap}/{max_len})")
                entry = defs[k]
                break
    # Try regex match for any word in the prompt against keys
    if not entry:
        import re
        prompt_words = [singularize(w) for w in normalize_key(term).split()]
        for k in defs:
            k_norm = normalize_key(k)
            for w in prompt_words:
                if re.search(rf'\b{re.escape(w)}\b', k_norm):
                    print(f"[DEBUG] Regex word match: '{w}' in '{k_norm}' (key: '{k}')")
                    entry = defs[k]
                    break
            if entry:
                break

    # Try direct match again
    if not entry:
        entry = defs.get(term)
        if entry:
            print(f"[DEBUG] Second direct match for term: '{term}'")
    # Try underscore-to-space match
    if not entry:
        for k in defs:
            if normalize_key(k) == normalize_key(term):
                print(f"[DEBUG] Underscore/space normalized match: '{term}' == '{k}'")
                entry = defs[k]
                break
    # Try fuzzy match for ordinal/numbered laws (e.g. '1st law of thermodynamics' to 'first law thermodynamics')
    if not entry:
        import re
        num_map = {'1st': 'first', '2nd': 'second', '3rd': 'third', '4th': 'fourth', '5th': 'fifth'}
        norm_term = normalize_key(term)
        for num, word in num_map.items():
            if num in norm_term:
                alt = norm_term.replace(num, word)
                for k in defs:
                    if normalize_key(k) == alt:
                        print(f"[DEBUG] Ordinal/numbered law match: '{norm_term}' -> '{alt}' == '{k}'")
                        entry = defs[k]
                        break
                if entry:
                    break
    # Try last token as term if still not found
    if not entry and len(lower_tokens) > 1:
        candidate = lower_tokens[-1]
        entry = defs.get(candidate)
        if entry:
            print(f"[DEBUG] Last token as term match: '{candidate}'")
    if not entry:
        print(f"[DEBUG] No match found for: '{term}' (tokens: {tokens})")
        return "I do not have a definition for that yet."

    # if isinstance(entry, str):
    #     print("BAD ENTRY (string where list expected):", term, entry)
    # if isinstance(entry, list):
    #     for i, item in enumerate(entry):
    #         if isinstance(item, str):
    #             print("BAD SENSE (string where dict expected):", term, item)

    # If there are multiple senses, ask for specificity
    # if isinstance(entry, list) and len(entry) > 1:
    #     return "Can you be more specific?"

    # Always pass a list to choose_sense
    if isinstance(entry, dict):
        sense = choose_sense([entry])
    else:
        sense = choose_sense(entry)
    # Handle both dict and string senses
    if isinstance(sense, dict):
        gloss = sense.get("gloss", "").strip()
        formula = sense.get("formula")
    elif isinstance(sense, str):
        gloss = sense.strip()
        formula = None
    else:
        gloss = ""
        formula = None

    # Use up to 5 sentences from the gloss and detail_phrases, weave them as a paragraph
    core_phrase, detail_phrases = split_gloss(gloss)
    sentences = []
    if core_phrase:
        sentences.append(core_phrase)
    # Add up to 4 more sentences from details
    for d in detail_phrases:
        if len(sentences) >= 5:
            break
        sentences.append(d)
    # If not enough, try to fill with related definitions as subtext
    while len(sentences) < 5:
        # Try to find a related term in the gloss or details
        found = False
        for t in defs.keys():
            if t == term:
                continue
            for s in sentences:
                if t in s and t in defs:
                    entry = defs[t]
                    if isinstance(entry, list):
                        sub_sense = entry[0]
                    elif isinstance(entry, dict):
                        sub_sense = entry
                    else:
                        sub_sense = ""
                    if isinstance(sub_sense, dict):
                        sub_gloss = sub_sense.get("gloss", "")
                    elif isinstance(sub_sense, str):
                        sub_gloss = sub_sense
                    else:
                        sub_gloss = ""
                    sub_core, sub_details = split_gloss(sub_gloss)
                    if sub_core and sub_core not in sentences:
                        sentences.append(sub_core)
                        found = True
                        break
            if found:
                break
        if not found:
            break
    # If still not enough, repeat or elaborate
    while len(sentences) < 5:
        sentences.append(f"This relates to {term} in various ways.")

    # Weave the sentences as a paragraph, alternating between main and subtext
    paragraph = ""
    for i, s in enumerate(sentences):
        if i == 0:
            paragraph += s
        else:
            paragraph += " " + s
    # If a formula or proof/instance is available, add it at the end
    if formula:
        paragraph += f" For example, the formula is {formula}."
    return paragraph

    # -------------------------------------------------------------
    # 4. Try to interpret arguments after the term as numbers
    #    for exec-based math entries, e.g. "addition 3 5"
    # -------------------------------------------------------------
    # Collect tokens after the first occurrence of the term
    try:
        term_index = lower_tokens.index(term)
    except ValueError:
        term_index = 0

    arg_tokens = tokens[term_index + 1 :]

    # Try to parse numeric arguments
    nums: List[float] = []
    numeric_parse_ok = True
    for tok in arg_tokens:
        try:
            nums.append(float(tok))
        except ValueError:
            numeric_parse_ok = False
            break

    if numeric_parse_ok and nums:
        math_result = parse_math_exec(defs, term, *nums)
        if math_result is not None:
            definition = build_definition_style(term, core_phrase, detail_phrases, formula)
            # Recursively resolve referenced terms in the gloss or formula
            referenced_terms = []
            for phrase in [gloss, formula] if formula else [gloss]:
                if phrase:
                    for t in defs.keys():
                        if t != term and t in phrase:
                            referenced_terms.append(t)
            recursive_defs = []
            for ref in set(referenced_terms):
                if ref in defs:
                    rec_core, rec_details = split_gloss(defs[ref][0].get("gloss", ""))
                    rec_formula = defs[ref][0].get("formula")
                    rec_def = build_definition_style(ref, rec_core, rec_details, rec_formula)
                    recursive_defs.append(f"    ↳ {rec_def}")
            if recursive_defs:
                definition += "\n" + "\n".join(recursive_defs)
            return f"{definition}\nResult: {math_result}"

    # -------------------------------------------------------------
    # 5. Pure definition output (moved to end unless question)
    # -------------------------------------------------------------
    definition = build_definition_style(term, core_phrase, detail_phrases, formula)
    referenced_terms = []
    for phrase in [gloss, formula] if formula else [gloss]:
        if phrase:
            for t in defs.keys():
                if t != term and t in phrase:
                    referenced_terms.append(t)
    recursive_defs = []
    for ref in set(referenced_terms):
        if ref in defs:
            rec_sense = defs[ref][0]
            if isinstance(rec_sense, dict):
                rec_gloss = rec_sense.get("gloss", "")
                rec_formula = rec_sense.get("formula")
            elif isinstance(rec_sense, str):
                rec_gloss = rec_sense.strip()
                rec_formula = None
            else:
                rec_gloss = ""
                rec_formula = None
            rec_core, rec_details = split_gloss(rec_gloss)
            rec_def = build_definition_style(ref, rec_core, rec_details, rec_formula)
            recursive_defs.append(f"    ↳ {rec_def}")
    if recursive_defs:
        definition += "\n" + "\n".join(recursive_defs)

    # If the input is a question, return the definition immediately
    if '?' in raw:
        return definition

    # Otherwise, return the definition last (after any math or assignment results)
    # (The rest of the function already returns early for math/assignment cases)
    return definition


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
