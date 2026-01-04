import os
import json
import re
from collections import Counter
from typing import Optional, Tuple

STOPWORDS = set([w.strip() for w in ("the and or is a an of in on for to with by as at from that which who whom where when why how be been are was were it its this these those but if then so".split())])


def normalize_token(tok):
    return re.sub(r'[^a-z0-9]', '', tok.lower())


def tokenize(text):
    toks = re.findall(r"\b\w+\b", (text or '').lower())
    toks = [normalize_token(t) for t in toks if t and normalize_token(t) and t not in STOPWORDS]
    return toks


def load_all_data(data_dir='data'):
    data = {}
    for fname in os.listdir(data_dir):
        if not fname.endswith('.json'):
            continue
        try:
            with open(os.path.join(data_dir, fname), 'r', encoding='utf8') as fh:
                data[fname] = json.load(fh)
        except Exception:
            data[fname] = {}
    return data


def find_entries(term, data_map):
    """Return list of (file, key, entry_obj) matching by key or synonyms."""
    nk = normalize_token(term)
    out = []
    for fname, data in data_map.items():
        for k, v in data.items():
            if normalize_token(k) == nk or nk in normalize_token(k):
                out.append((fname, k, v))
                continue
            # check synonyms/gloss
            if isinstance(v, list):
                for o in v:
                    if isinstance(o, dict):
                        syns = o.get('synonyms', [])
                        gloss = o.get('gloss','')
                        for s in syns:
                            if normalize_token(s) == nk or nk in normalize_token(s):
                                out.append((fname, k, o))
                                break
                        if nk in ' '.join(tokenize(gloss)):
                            out.append((fname, k, o))
            elif isinstance(v, dict):
                syns = v.get('synonyms', [])
                gloss = v.get('gloss','')
                for s in syns:
                    if normalize_token(s) == nk or nk in normalize_token(s):
                        out.append((fname, k, v))
                        break
                if nk in ' '.join(tokenize(gloss)):
                    out.append((fname, k, v))
    # keep unique by (fname,key)
    uniq = {}
    for f,k,v in out:
        uniq[(f,k)] = (f,k,v)
    return list(uniq.values())


def entry_keywords(entry_obj):
    # extract tokens from gloss and synonyms and keys
    toks = []
    if isinstance(entry_obj, dict):
        toks += tokenize(entry_obj.get('gloss',''))
        for s in entry_obj.get('synonyms', []):
            toks += tokenize(s)
    elif isinstance(entry_obj, list):
        for o in entry_obj:
            if isinstance(o, dict):
                toks += tokenize(o.get('gloss',''))
                for s in o.get('synonyms',[]):
                    toks += tokenize(s)
    else:
        toks += tokenize(str(entry_obj))
    return toks


def inclusion_score(broad_entry, narrow_entry):
    """Estimate how much broad_entry's definition includes narrow_entry.

    Returns score in [0,1] representing fraction of narrow tokens covered by broad tokens.
    """
    broad = set(entry_keywords(broad_entry))
    narrow = entry_keywords(narrow_entry)
    if not narrow:
        return 0.0
    if not broad:
        return 0.0
    match = sum(1 for t in narrow if t in broad)
    return match / max(1, len(narrow))


def relation_between_terms(a, b, data_dir='data', include_threshold=0.6, overlap_threshold=0.25):
    """Return a relation dict describing equality/inclusion/overlap/distinct.

    relation types: 'equal' (synonym or identical), 'a_includes_b', 'b_includes_a', 'overlap', 'distinct'
    """
    data = load_all_data(data_dir)
    found_a = find_entries(a, data)
    found_b = find_entries(b, data)

    # Helper: parse explicit year or year-range from a plain term like '1914' or '1914-1918'
    def _parse_year_range_from_term(term) -> Optional[Tuple[int,int]]:
        nums = re.findall(r"-?\d{1,4}", term)
        if not nums:
            return None
        years = [int(n) for n in nums]
        if len(years) == 1:
            return (years[0], years[0])
        return (min(years), max(years))

    def _overlap_frac(s1,e1,s2,e2):
        start = max(s1,s2)
        end = min(e1,e2)
        if end < start:
            return 0.0
        inter = end - start + 1
        union = max(e1,e2) - min(s1,s2) + 1
        return inter / union

    # If either term encodes a year/range explicitly, compute temporal relation first
    range_a = _parse_year_range_from_term(a)
    range_b = _parse_year_range_from_term(b)

    # Collect ranges from resolved entries (use start_year/end_year or year)
    def _collect_ranges(found_list):
        ranges = []
        for fname, key, val in found_list:
            # records may be dict or list
            candidates = []
            if isinstance(val, dict):
                candidates.append(val)
            elif isinstance(val, list):
                for v in val:
                    if isinstance(v, dict):
                        candidates.append(v)
            for rec in candidates:
                sy = rec.get('start_year')
                ey = rec.get('end_year')
                if sy is None and 'year' in rec:
                    sy = rec.get('year')
                    ey = rec.get('year')
                if sy is not None and ey is not None:
                    try:
                        ranges.append((int(sy), int(ey), f"{fname}:{key}"))
                    except Exception:
                        continue
        return ranges

    ranges_a = _collect_ranges(found_a)
    ranges_b = _collect_ranges(found_b)

    # If we have explicit term ranges or entry ranges, evaluate temporal overlap
    if range_a or range_b or ranges_a or ranges_b:
        # seed lists with explicit term ranges if present
        ta = []
        tb = []
        if range_a:
            ta.append((range_a[0], range_a[1], 'term'))
        ta.extend(ranges_a)
        if range_b:
            tb.append((range_b[0], range_b[1], 'term'))
        tb.extend(ranges_b)
        best = 0.0
        best_pair = None
        for s1,e1,src1 in ta:
            for s2,e2,src2 in tb:
                frac = _overlap_frac(s1,e1,s2,e2)
                if frac > best:
                    best = frac
                    best_pair = (s1,e1,src1,s2,e2,src2)
        if best_pair and best > 0.0:
            s1,e1,src1,s2,e2,src2 = best_pair
            # inclusive checks
            if s1 <= s2 and e1 >= e2 and (e1 - s1) >= (e2 - s2):
                return {'relation':'a_includes_b', 'score': best, 'reason': f'temporal include: {src1} covers {src2} ({best:.2f})'}
            if s2 <= s1 and e2 >= e1 and (e2 - s2) >= (e1 - s1):
                return {'relation':'b_includes_a', 'score': best, 'reason': f'temporal include: {src2} covers {src1} ({best:.2f})'}
            # if near-equal span and overlap high, mark equal
            if best > 0.85 and abs((e1 - s1) - (e2 - s2)) <= 5:
                return {'relation':'equal', 'score': best, 'reason': f'temporal match between {src1} and {src2} ({best:.2f})'}
            return {'relation':'overlap', 'score': best, 'reason': f'temporal overlap between {src1} and {src2} ({best:.2f})'}

    # if exact same normalized name
    if normalize_token(a) == normalize_token(b):
        return {'relation':'equal', 'reason':'identical tokens'}

    # check synonyms / exact gloss equality
    for fa, ka, va in found_a:
        kws_a = set(entry_keywords(va))
        for fb, kb, vb in found_b:
            kws_b = set(entry_keywords(vb))
            # identical gloss or large symmetric overlap
            if ka == kb and fa == fb:
                return {'relation':'equal', 'reason':f'same entry in {fa}:{ka}'}
            # synonyms: token overlap near 1.0
            inter = len(kws_a & kws_b)
            denom = max(1, min(len(kws_a), len(kws_b)))
            if denom > 0 and (inter / denom) > 0.85:
                return {'relation':'equal', 'reason':f'high token overlap between {ka} and {kb}'}

    # check inclusion both ways
    best_a_in_b = 0.0
    best_b_in_a = 0.0
    for fa, ka, va in found_a:
        for fb, kb, vb in found_b:
            s_ab = inclusion_score(va, vb)
            s_ba = inclusion_score(vb, va)
            best_a_in_b = max(best_a_in_b, s_ab)
            best_b_in_a = max(best_b_in_a, s_ba)

    if best_a_in_b >= include_threshold and best_b_in_a >= include_threshold:
        return {'relation':'equal', 'reason':f'both definitions include the other (scores {best_a_in_b:.2f}/{best_b_in_a:.2f})'}
    if best_a_in_b >= include_threshold:
        return {'relation':'a_includes_b', 'score': best_a_in_b, 'reason': f'{a} definition covers {best_a_in_b:.2f} of {b}'}
    if best_b_in_a >= include_threshold:
        return {'relation':'b_includes_a', 'score': best_b_in_a, 'reason': f'{b} definition covers {best_b_in_a:.2f} of {a}'}

    # partial overlap
    # compute token overlap across best pair
    best_overlap = 0.0
    for fa, ka, va in found_a:
        for fb, kb, vb in found_b:
            sa = set(entry_keywords(va))
            sb = set(entry_keywords(vb))
            if not sa or not sb:
                continue
            inter = len(sa & sb)
            j = inter / max(1, len(sa | sb))
            best_overlap = max(best_overlap, j)
    if best_overlap >= overlap_threshold:
        return {'relation':'overlap', 'score': best_overlap, 'reason': f'Jaccard overlap {best_overlap:.2f}'}

    return {'relation':'distinct', 'reason':'low overlap and no inclusion detected'}


def cli(argv):
    # simple CLI: verify <termA> <termB>
    if not argv or len(argv) < 2:
        print('Usage: verify <termA> <termB>')
        return 2
    a = argv[0]
    b = argv[1]
    res = relation_between_terms(a, b)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == '__main__':
    import sys
    raise SystemExit(cli(sys.argv[1:]))
