import os
import re
import json
from collections import Counter
import math

STOPWORDS = {
    'the','and','or','is','a','an','of','in','on','for','to','with','by','as','at','from','that','which','who','whom','where','when','why','how','be','been','are','was','were','it','its','this','these','those','but','if','then','so'
}

def normalize(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())

def fragment_prompt(prompt):
    # Split into sentences, then into clause-like fragments
    sentences = re.split(r'[\.\?!]\s+', prompt.strip())
    fragments = []
    for s in sentences:
        # split on commas, semicolons, and common relative words
        parts = re.split(r',|;|:|\b(which|that|who|where|when|because|although|while)\b', s)
        for p in parts:
            if not p:
                continue
            p = p.strip()
            if p:
                fragments.append(p)
    return fragments

def extract_keywords(fragment, top_n=6):
    tokens = re.findall(r"\b\w+\b", fragment.lower())
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    if not tokens:
        return []
    counts = Counter(tokens)
    return [w for w,_ in counts.most_common(top_n)]

def load_data(data_dir='data'):
    data_map = {}
    for fname in os.listdir(data_dir):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(data_dir, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data_map[fname] = json.load(f)
        except Exception:
            data_map[fname] = {}
    return data_map

def find_matches(keywords, data_map):
    matches = []
    for kw in keywords:
        nk = normalize(kw)
        for fname, data in data_map.items():
            for entry_key, entry_val in data.items():
                ne = normalize(entry_key)
                # match against entry key
                if nk and nk in ne:
                    matches.append((kw, fname, entry_key, entry_val, 'key'))
                    continue
                # match against synonyms and gloss
                if isinstance(entry_val, list):
                    for obj in entry_val:
                        if isinstance(obj, dict):
                            syns = obj.get('synonyms', [])
                            gloss = obj.get('gloss', '')
                            for s in syns:
                                if nk and nk in normalize(s):
                                    matches.append((kw, fname, entry_key, obj, 'synonym'))
                                    break
                            if nk and nk in normalize(gloss):
                                matches.append((kw, fname, entry_key, obj, 'gloss'))
                elif isinstance(entry_val, dict):
                    syns = entry_val.get('synonyms', [])
                    gloss = entry_val.get('gloss', '')
                    for s in syns:
                        if nk and nk in normalize(s):
                            matches.append((kw, fname, entry_key, entry_val, 'synonym'))
                            break
                    if nk and nk in normalize(gloss):
                        matches.append((kw, fname, entry_key, entry_val, 'gloss'))
    return matches

def classify_family(gloss_or_entry):
    s = ''
    if isinstance(gloss_or_entry, dict):
        s = (gloss_or_entry.get('gloss','') or '')
    else:
        s = str(gloss_or_entry)
    s = s.lower()
    if 'theorem' in s or 'proof' in s:
        return 'theorem'
    if 'formula' in s or '=' in s or 'derivative' in s or 'integral' in s:
        return 'formula'
    if 'metabolite' in s or 'intermediate' in s or 'enzyme' in s:
        return 'metabolite'
    if 'drug' in s or 'analgesic' in s or 'recreational' in s:
        return 'drug'
    if 'electron' in s or 'ion' in s or 'nucleus' in s or 'quark' in s:
        return 'atomic'
    if 'matrix' in s or 'vector' in s or 'matrix' in s:
        return 'linear_algebra'
    return 'general'

def extract_order(gloss_or_entry):
    # Try to find a short formula-like substring in the gloss
    s = ''
    if isinstance(gloss_or_entry, dict):
        s = (gloss_or_entry.get('gloss','') or '')
    else:
        s = str(gloss_or_entry)
    s = s.strip()
    # look for patterns like x = ... or contains numbers/chem formulas
    m = re.search(r"([A-Za-z0-9()\[\]{}.+\-^_=\/]+\s*=\s*[A-Za-z0-9().+\-^_/]+)", s)
    if m:
        return m.group(1)
    # fallback to short gloss snippet
    return (s[:200] + '...') if len(s) > 200 else s

GROUP_MAP = {
    'math': {'algebra.json','linear_algebra.json','calculus.json','math.json','geometry.json','complex_numbers.json','probability.json','statistics.json','trigonometry.json','vectors.json'},
    'science': {'biology.json','chemistry.json','physics.json','thermodynamics.json'},
    'code': {'code_dictionary.json'},
    'definitions': {'definitions.json'},
    'other': set()
}

def group_for_file(fname):
    for g, files in GROUP_MAP.items():
        if fname in files:
            return g
    return 'other'

def build_taxonomy(match):
    # match: (kw, fname, entry_key, entry_val, matched_field)
    kw, fname, entry_key, entry_val, matched_field = match
    kingdom = group_for_file(fname)
    phylum = fname.replace('.json','')
    family = classify_family(entry_val)
    order = extract_order(entry_val)
    variable = normalize(entry_key)
    # type is the most specific value found for the match
    if matched_field == 'synonym':
        typ = 'synonym'
        value = entry_val.get('synonyms', [])
    elif matched_field == 'gloss':
        typ = 'gloss'
        value = entry_val.get('gloss','') if isinstance(entry_val, dict) else str(entry_val)
    else:
        typ = 'entry'
        if isinstance(entry_val, list):
            # pick first gloss if present
            first = entry_val[0] if entry_val else {}
            value = first.get('gloss') if isinstance(first, dict) else first
        elif isinstance(entry_val, dict):
            value = entry_val.get('gloss','')
        else:
            value = str(entry_val)
    return {
        'kingdom': kingdom,
        'phylum': phylum,
        'family': family,
        'order': order,
        'variable': variable,
        'type': typ,
        'value': value
    }

def analyze(prompt, data_dir='data'):
    fragments = fragment_prompt(prompt)
    data_map = load_data(data_dir)
    result = {'prompt': prompt, 'fragments': []}
    for frag in fragments:
        kws = extract_keywords(frag)
        matches = find_matches(kws, data_map)
        taxons = [build_taxonomy(m) for m in matches]
        result['fragments'].append({'fragment': frag, 'keywords': kws, 'matches': taxons})
    return result

if __name__ == '__main__':
    import sys
    prompt = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else input('Prompt: ')
    out = analyze(prompt)
    print(json.dumps(out, indent=2, ensure_ascii=False))


def _score_taxon(t):
    score = 0
    if t.get('family') and t.get('family') != 'general':
        score += 3
    if t.get('type') == 'gloss':
        score += 2
    if t.get('type') == 'synonym':
        score += 1
    v = t.get('value')
    if v:
        try:
            ln = len(str(v))
            score += min(3, ln // 50)
        except Exception:
            pass
    if t.get('variable') and len(t.get('variable', '')) > 3:
        score += 1
    return score


def render_response(result, max_items=6, positivity=True):
    """Create a friendly, rhetorical response from the taxonomy analysis.

    The renderer collects all matches, scores them by specificity and depth,
    then composes short, positive sentences that reference the fragment and
    the taxonomy placement (kingdom/phylum/family/order/variable/type/value).
    """
    all_taxons = []
    for frag in result.get('fragments', []):
        for m in frag.get('matches', []):
            mt = m.copy()
            mt['fragment'] = frag.get('fragment')
            mt['keywords'] = frag.get('keywords', [])
            all_taxons.append(mt)

    if not all_taxons:
        return "I couldn't find close matches in the available dictionaries."

    scored = [( _score_taxon(t), t) for t in all_taxons]
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [t for s, t in scored[:max_items]]

    lines = []
    if positivity:
        lines.append("Great — here are some helpful connections I found:")
    else:
        lines.append("Here are the connections I found:")

    for t in picked:
        kingdom = t.get('kingdom', '')
        phylum = t.get('phylum', '')
        family = t.get('family', '')
        order = t.get('order', '')
        variable = t.get('variable', '')
        typ = t.get('type', '')
        value = t.get('value', '')
        frag = (t.get('fragment') or '').strip()
        kws = ', '.join(t.get('keywords', []))

        # Friendly phrasing
        sentence = f"In {kingdom} ({phylum}), {variable} — a {family} — is expressed as: {str(value)}"
        if frag:
            sentence += f"; this comes from the fragment: \"{frag}\""
        if kws:
            sentence += f" (keywords: {kws})"
        lines.append(sentence)

    if positivity:
        lines.append("I hope this helps — happy to explore any part more deeply!")
    else:
        lines.append("Let me know if you'd like further details.")

    return "\n\n".join(lines)


def _render_from_taxons(taxons, positivity=True):
    """Render a friendly block from a provided list of taxons (already selected).

    This is a helper so variation steps can render focused outputs.
    """
    if not taxons:
        return "(no specific taxons to render)"
    # pick up to 6 items by score
    scored = [( _score_taxon(t), t) for t in taxons]
    scored.sort(key=lambda x: x[0], reverse=True)
    picked = [t for s, t in scored[:6]]

    lines = []
    if positivity:
        lines.append("Here's a focused view:")
    else:
        lines.append("Focused view:")

    for t in picked:
        kingdom = t.get('kingdom', '')
        phylum = t.get('phylum', '')
        family = t.get('family', '')
        order = t.get('order', '')
        variable = t.get('variable', '')
        typ = t.get('type', '')
        value = t.get('value', '')
        frag = (t.get('fragment') or '').strip()
        kws = ', '.join(t.get('keywords', []))

        sentence = f"In {kingdom} ({phylum}), {variable} — a {family} —: {str(value)}"
        if frag:
            sentence += f" (from: '{frag}')"
        if kws:
            sentence += f" [keywords: {kws}]"
        lines.append(sentence)

    if positivity:
        lines.append("Lovely — we can rotate through these to offer varied perspectives.")
    else:
        lines.append("Ask to expand any line for details.")
    return "\n\n".join(lines)


def _poetic_sentence_from_taxon(t):
    """Compose a single poetic sentence that uses the taxonomy nouns
    and ends by pinning the `type`/`value` as the final emphasized point.
    """
    kingdom = t.get('kingdom') or 'domain'
    phylum = t.get('phylum') or ''
    family = t.get('family') or 'thing'
    order = (t.get('order') or '').strip()
    variable = t.get('variable') or 'this topic'
    typ = t.get('type') or 'type'
    value = t.get('value') or ''

    # short snippets for order/value
    order_snip = order.split('\n')[0].split('.')[0]
    if len(order_snip) > 140:
        order_snip = order_snip[:137].rstrip() + '...'

    value_snip = str(value)
    if len(value_snip) > 220:
        value_snip = value_snip[:217].rstrip() + '...'

    # Build a serrated, plunging sentence that ends with the type:value pin.
    parts = []
    parts.append(f"Plunging into the {kingdom} of {phylum},") if phylum else parts.append(f"Plunging into the {kingdom},")
    parts.append(f"a {family} named {variable}")
    if order_snip:
        parts.append(f"winds through {order_snip}")
    # small serpentine clause
    parts.append("a serpentine of rightly placed words that evaluates the question")
    # final pin
    if value_snip:
        parts.append(f"and pins the answer as the {typ}: {value_snip}.")
    else:
        parts.append(f"and points toward the {typ} as the final pin.")

    # join with commas to create a flowing, single sentence
    sentence = ', '.join(parts)
    # ensure proper termination
    if not sentence.endswith('.'):
        sentence = sentence.rstrip() + '.'
    return sentence


def generate_poetic_variations(result, steps=6, positivity=True, reverse=False):
    """Generate poetic one-sentence variations that emphasize taxonomy nouns
    and place the `type`/`value` as the final 'pin'. Supports an optional
    reverse traversal of the variable list to follow a reverse-taxonomy delta.
    """
    # collect taxons
    all_taxons = []
    for frag in result.get('fragments', []):
        for m in frag.get('matches', []):
            mt = m.copy()
            mt['fragment'] = frag.get('fragment')
            mt['keywords'] = frag.get('keywords', [])
            all_taxons.append(mt)

    if not all_taxons:
        return ["No matches found to generate variations."]

    # create unique variables but keep representative taxon per variable
    vars_map = {}
    for t in all_taxons:
        v = t.get('variable') or ''
        if not v:
            continue
        if v not in vars_map:
            vars_map[v] = t

    variables = list(vars_map.keys())
    if not variables:
        return [render_response(result, max_items=6, positivity=positivity)]

    # order variables by a depth metric (reuse _score_taxon approximate)
    variables.sort(key=lambda vv: _score_taxon(vars_map[vv]), reverse=True)
    if reverse:
        variables = variables[::-1]

    nvars = len(variables)
    variations = []
    for step in range(steps):
        # phase-based sampling (cosine) but allow reverse ordering via `reverse` above
        phase = 2 * math.pi * (step / max(1, steps))
        s = math.cos(phase)
        idx = int(round(((s + 1) / 2) * (nvars - 1)))
        chosen_var = variables[idx]
        taxon = vars_map.get(chosen_var)
        if not taxon:
            # fallback to top scored taxon
            scored = [( _score_taxon(t), t) for t in all_taxons]
            scored.sort(key=lambda x: x[0], reverse=True)
            taxon = scored[0][1]

        sentence = _poetic_sentence_from_taxon(taxon)
        header = f"Variation {step+1}/{steps} — {chosen_var}"
        variations.append(header + "\n\n" + sentence)

    return variations


def generate_variations_conditional(result, steps=6, positivity=True, minimal=True, reverse=False, anchor_level='phylum', temperature=0.2, verbosity='long'):
    """Generate concise, conditionally-argumentative sentences using taxonomy nouns.

    - `minimal=True` avoids theatrical templates and uses only a few connective words.
    - Each variation uses the taxon's fields (kingdom, phylum, family, order, variable, type, value)
      to build a short argumentative sentence that ends by stating the `type:value`.
    - `reverse=True` traverses variables in reverse order to support reverse-taxonomy delta.
    """
    all_taxons = []
    for frag in result.get('fragments', []):
        for m in frag.get('matches', []):
            mt = m.copy()
            mt['fragment'] = frag.get('fragment')
            mt['keywords'] = frag.get('keywords', [])
            all_taxons.append(mt)

    if not all_taxons:
        return ["No matches found to generate variations."]

    # representative taxon per variable
    vars_map = {}
    for t in all_taxons:
        v = t.get('variable') or ''
        if v and v not in vars_map:
            vars_map[v] = t

    # If anchor requested, determine anchor from highest scored taxon
    variables = list(vars_map.keys())
    if anchor_level in ('phylum','kingdom','family') and variables:
        # find top-scoring taxon
        scored_all = [( _score_taxon(t), t) for t in all_taxons]
        scored_all.sort(key=lambda x: x[0], reverse=True)
        top = scored_all[0][1]
        anchor_val = top.get(anchor_level)
        if anchor_val:
            # filter to same anchor
            anchored = {k: v for k, v in vars_map.items() if v.get(anchor_level) == anchor_val}
            if anchored:
                vars_map = anchored
                variables = list(vars_map.keys())
    if not variables:
        return [render_response(result, max_items=6, positivity=positivity)]

    # order by score and optionally reverse
    variables.sort(key=lambda vv: _score_taxon(vars_map[vv]), reverse=True)
    if reverse:
        variables = variables[::-1]

    nvars = len(variables)
    out = []

    # Templates to introduce variety. Keep them short when `minimal`.
    minimal_templates = [
        "{head} — {variable}{ctx_part} — => {typ}: {value}",
        "{variable}{ctx_part} — leads to {typ}: {value}",
        "{head}: {variable}{ctx_part} -> {typ}: {value}",
        "{variable} ({head}) — {typ}: {value}"
    ]
    verbose_templates = [
        "Given {head}, {variable}{ctx_part}; therefore the {typ} is {value}.",
        "Considering {ctx}, the {family} {variable} suggests {typ}: {value}.",
        "In {phylum}, {variable} (a {family}) points to {typ}: {value}."
    ]

    used_vars = []
    for step in range(steps):
        # pick a variable index that rotates deterministically to cover different variables
        if nvars == 0:
            break
        # base index from cosine to keep familiar sampling, then offset by step to avoid repeats
        phase = 2 * math.pi * (step / max(1, steps))
        s = math.cos(phase)
        base_idx = int(round(((s + 1) / 2) * (nvars - 1)))
        idx = (base_idx + step) % nvars
        chosen = variables[idx]
        used_vars.append(chosen)

        t = vars_map.get(chosen)
        if not t:
            scored = [( _score_taxon(x), x) for x in all_taxons]
            scored.sort(key=lambda x: x[0], reverse=True)
            t = scored[0][1]

        kingdom = t.get('kingdom') or ''
        phylum = t.get('phylum') or ''
        family = t.get('family') or ''
        order = (t.get('order') or '').split('\n')[0].split('.')[0].strip()
        variable = t.get('variable') or chosen
        typ = t.get('type') or 'type'
        value = str(t.get('value') or '')
        value = value.replace('\n', ' ').strip()
        val_snip = value if len(value) <= 200 else value[:197].rstrip() + '...'

        head_parts = []
        if family and family != 'general':
            head_parts.append(family)
        if phylum and phylum not in (family, ''):
            head_parts.append(phylum)
        head = ', '.join(head_parts) if head_parts else (kingdom or '')

        ctx = order or (t.get('fragment') or '').split('.')[0].strip()
        if not ctx and t.get('keywords'):
            ctx = (t.get('keywords') or [''])[0]
        ctx_part = (f" via {ctx}" if ctx else '')

        # Select template set
        # Decide template selection influenced by temperature and verbosity
        if temperature <= 0.2:
            templates = minimal_templates if minimal else verbose_templates
        else:
            # when warmer, favor verbose templates more often
            templates = (minimal_templates if verbosity == 'short' else verbose_templates) if temperature < 0.6 else (verbose_templates + minimal_templates)
        tpl = templates[step % len(templates)]

        # Build sentence
        sentence = tpl.format(
            head=head,
            phylum=phylum,
            family=family,
            variable=variable,
            ctx_part=ctx_part,
            ctx=ctx,
            typ=typ,
            value=val_snip
        )

        # If only one variable appears repeatedly, vary which field we emphasize
        if nvars == 1:
            # cycle emphasis: variable, head, ctx, value
            mode = step % 4
            if mode == 0:
                sentence = f"{variable} — {typ}: {val_snip}"
            elif mode == 1 and head:
                sentence = f"{head} — {variable} — {typ}: {val_snip}"
            elif mode == 2 and ctx:
                sentence = f"{variable} via {ctx} — {typ}: {val_snip}"
            else:
                sentence = f"{variable} — {typ}: {val_snip}"
        else:
            # when multiple variables and temperature>0.5, add extra clause occasionally
            if temperature > 0.6 and (step % 3 == 0):
                extra = ''
                if verbosity == 'long' and ctx:
                    extra = f" (context: {ctx})"
                sentence = sentence.rstrip('.') + extra + '.'

        header = f"Variation {step+1}/{steps} — {variable}"
        out.append(header + "\n\n" + sentence)

    return out


def generate_variations(result, steps=6, positivity=True):
    """Generate a list of rendered responses by traversing variables using a sine wave.

    - Collects all taxons from `result`.
    - Builds an ordered unique list of `variable` values (genus).
    - For each step, picks a variable index via a sine mapping and renders a focused view.
    """
    all_taxons = []
    for frag in result.get('fragments', []):
        for m in frag.get('matches', []):
            mt = m.copy()
            mt['fragment'] = frag.get('fragment')
            mt['keywords'] = frag.get('keywords', [])
            all_taxons.append(mt)

    if not all_taxons:
        return ["No matches found to generate variations."]

    # Unique variables in deterministic order
    variables = []
    seen = set()
    for t in all_taxons:
        v = t.get('variable') or ''
        if v and v not in seen:
            seen.add(v)
            variables.append(v)
    if not variables:
        # fallback to variables derived from entry keys
        variables = [t.get('variable','') for t in all_taxons if t.get('variable')]
        variables = list(dict.fromkeys(variables))

    nvars = len(variables)
    if nvars == 0:
        # nothing to vary; render overall response
        return [render_response(result, max_items=6, positivity=positivity)]

    variations = []
    for step in range(steps):
        phase = 2 * math.pi * (step / max(1, steps))
        # cosine sampling: cos value in [-1,1] -> mapped to index [0, nvars-1]
        s = math.cos(phase)
        idx = int(round(((s + 1) / 2) * (nvars - 1)))
        chosen_var = variables[idx]
        # Filter taxons for chosen variable; if none, choose top-scoring
        filtered = [t for t in all_taxons if t.get('variable') == chosen_var]
        if not filtered:
            # pick ones with variable close in name
            filtered = [t for t in all_taxons if chosen_var in (t.get('variable') or '')]
        if not filtered:
            # fallback to top 3
            scored = [( _score_taxon(t), t) for t in all_taxons]
            scored.sort(key=lambda x: x[0], reverse=True)
            filtered = [t for s, t in scored[:3]]

        header = f"Variation {step+1}/{steps} — focusing on genus (variable): '{chosen_var}'"
        body = _render_from_taxons(filtered, positivity=positivity)
        variations.append(header + "\n\n" + body)

    return variations


def pipeline_response(prompt, data_dir='data', settings=None):
    """Run the 10-step taxonomic grammar pipeline described by the user.

    Implements: fragmenting, verb/subject extraction, dictionary scoring, clarifiers,
    main taxon selection, family-anchored related perspectives, and a smoothed narrative.
    """
    settings = settings or {}
    anchor_level = settings.get('anchor_level', 'phylum')
    steps = settings.get('variations_steps', 4)
    minimal = settings.get('minimal_templates', True)
    temperature = settings.get('temperature', 0.2)
    positivity = settings.get('positivity', True)

    fragments = fragment_prompt(prompt)
    data_map = load_data(data_dir)

    out = {'prompt': prompt, 'fragments': []}

    # collect overall matches and richer verb/noun extraction
    file_counts = {}
    file_scores = {}
    all_matches = []
    for frag in fragments:
        kws = extract_keywords(frag)
        verbs = re.findall(r"\b(is|are|was|were|be|has|have|does|do|flows|runs|falls|sits|stands|sprays|stalk|stalks|spray|run|jump|walk|swim)\b", frag.lower())
        subj_matches = re.findall(r"(\b[ A-Za-z]{3,40}?\b)\s+(is|are|was|were|sprays|stalks|runs|flows)\b", frag)
        subjects = [s[0].strip() for s in subj_matches]
        matches = find_matches(kws, data_map)
        taxons = [build_taxonomy(m) for m in matches]
        for m in matches:
            fname = m[1]
            all_matches.append(m)
            file_counts[fname] = file_counts.get(fname, 0) + 1
            try:
                t = build_taxonomy(m)
                sc = _score_taxon(t)
            except Exception:
                sc = 1
            file_scores[fname] = file_scores.get(fname, 0) + sc
        out['fragments'].append({'fragment': frag, 'keywords': kws, 'verbs': verbs, 'subjects': subjects, 'matches': taxons})

    # choose the dictionary with the highest weighted score as topic decider
    top_file = None
    if file_scores:
        def score_bias(item):
            fname, score = item
            bias = 1.0
            if fname.startswith('code') or fname == 'code_dictionary.json':
                bias = 0.7
            return score * bias

        top_file = max(file_scores.items(), key=score_bias)[0]
    elif file_counts:
        top_file = max(file_counts.items(), key=lambda x: x[1])[0]

    # collect clarifiers from that dictionary
    clarifiers = []
    if top_file and top_file in data_map:
        data = data_map[top_file]
        keys_seen = set([m[2] for m in all_matches if m[1] == top_file])
        for k in keys_seen:
            val = data.get(k)
            if isinstance(val, list) and val:
                for o in val:
                    if isinstance(o, dict):
                        clarifiers.append({'key': k, 'gloss': o.get('gloss',''), 'synonyms': o.get('synonyms',[])})
                        break
            elif isinstance(val, dict):
                clarifiers.append({'key': k, 'gloss': val.get('gloss',''), 'synonyms': val.get('synonyms',[])})
            else:
                clarifiers.append({'key': k, 'gloss': str(val)})

    # pick a main taxon: highest scored taxon from all matches (prefer top_file)
    all_taxons = [build_taxonomy(m) for m in all_matches]
    main_taxon = None
    if all_taxons:
        scored = [( _score_taxon(t), t) for t in all_taxons]
        scored.sort(key=lambda x: x[0], reverse=True)
        if top_file:
            for s, t in scored:
                ph = t.get('phylum') or ''
                if ph + '.json' == top_file or ph == top_file.replace('.json',''):
                    main_taxon = t
                    break
        if not main_taxon:
            main_taxon = scored[0][1]

    # compose kingdom->...->type path
    path = None
    if main_taxon:
        path = {k: main_taxon.get(k) for k in ('kingdom','phylum','family','order','variable','type','value')}

    # find related items in the same family via cosine sampling
    related_texts = []
    if main_taxon:
        family = main_taxon.get('family')
        temp_fragments = []
        for frag in out['fragments']:
            for t in frag.get('matches', []):
                if t.get('family') == family:
                    temp_fragments.append({'fragment': frag.get('fragment'), 'keywords': frag.get('keywords', []), 'matches': [t]})
        temp_result = {'prompt': prompt, 'fragments': temp_fragments}
        try:
            texts = generate_variations_conditional(temp_result, steps=steps, positivity=positivity, minimal=minimal, reverse=settings.get('reverse', False), anchor_level='family', temperature=temperature, verbosity=settings.get('verbosity','long'))
            related_texts = texts
        except Exception:
            related_texts = []

    # connect fragment with responses (before/after)
    for frag in out['fragments']:
        best = None
        best_score = -1
        for t in frag.get('matches', []):
            s = _score_taxon(t)
            if s > best_score:
                best = t
                best_score = s
        if best:
            resp = _render_from_taxons([best], positivity=positivity)
        else:
            resp = "(no clear match)"
        frag['response_fragment'] = {'before': frag.get('fragment'), 'response': resp, 'after': ''}

    # final textual response: smoother narrative from kingdom->type, include clarifiers and related texts
    def _smooth_value_text(v):
        if not v:
            return ''
        s = str(v).strip()
        if len(s) > 400:
            s = s[:397].rstrip() + '...'
        s = s[0].upper() + s[1:]
        return s

    def _smooth_narrative(main_taxon, clarifiers, related_texts):
        if not main_taxon:
            return "I couldn't identify a confident topic from the available dictionaries."
        k = main_taxon.get('kingdom')
        p = main_taxon.get('phylum')
        f = main_taxon.get('family')
        v = main_taxon.get('variable')
        typ = main_taxon.get('type')
        val = _smooth_value_text(main_taxon.get('value'))

        parts = []
        parts.append(f"Focusing on {k} → {p} → {f},")
        parts.append(f"the concept '{v}' resolves to {typ}.")
        if val:
            parts.append(val)
        if clarifiers:
            cl_lines = []
            for c in clarifiers[:4]:
                syns = c.get('synonyms') or []
                cl_lines.append(f"{c.get('key')}: {c.get('gloss') or '(no gloss)'}" + (f" (synonyms: {', '.join(syns)})" if syns else ""))
            parts.append("Clarifiers: " + '; '.join(cl_lines))
        if related_texts:
            parts.append("Related perspectives:")
            for t in related_texts[:4]:
                parts.append(str(t))
        return '\n\n'.join(parts)

    text_narrative = _smooth_narrative(main_taxon, clarifiers, related_texts)

    out['topic_file'] = top_file
    out['main_taxon'] = main_taxon
    out['clarifiers'] = clarifiers
    out['related'] = related_texts
    out['text_response'] = text_narrative
    return out
