import json
import os
from typing import Dict, List, Tuple

ROOT = os.path.dirname(__file__)
HISTORY_PATH = os.path.join(ROOT, 'data', 'history.json')


def load_history(path: str = None) -> Dict:
    """Load history JSON and return as dict."""
    p = path or HISTORY_PATH
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)


def _entry_year_range(entry: Dict) -> Tuple[int, int]:
    """Return (start_year, end_year) for an entry dict, using fallbacks.

    Assumes numeric keys `start_year` and `end_year` when available.
    """
    s = entry.get('start_year')
    e = entry.get('end_year')
    if s is None and 'year' in entry:
        # single-year event
        s = entry.get('year')
        e = entry.get('year')
    if s is None or e is None:
        # Fallback: try to parse 'period' crudely (not robust but pragmatic)
        period = entry.get('period', '')
        parts = [p.strip() for p in period.replace('c.', '').split('-') if p.strip()]
        try:
            if len(parts) == 2:
                s = int(parts[0])
                e = int(parts[1])
        except Exception:
            if s is None:
                s = -9999
            if e is None:
                e = 9999
    return int(s), int(e)


def find_entries_covering_year(year: int, history: Dict = None) -> List[Tuple[str, Dict]]:
    """Return list of (key, entry_dict) where the entry covers the given year."""
    h = history or load_history()
    matches = []
    for key, records in h.items():
        # normalize records: some keys map to dicts of lists (e.g., timeline_examples)
        record_list = []
        if isinstance(records, dict):
            for v in records.values():
                if isinstance(v, list):
                    record_list.extend(v)
        elif isinstance(records, list):
            record_list = records
        else:
            continue

        for rec in record_list:
            if not isinstance(rec, dict):
                continue
            s, e = _entry_year_range(rec)
            if s <= year <= e:
                matches.append((key, rec))
    return matches


def _overlap_fraction(a_start: int, a_end: int, b_start: int, b_end: int) -> float:
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    if end < start:
        return 0.0
    intersect = end - start + 1
    union = max(a_end, b_end) - min(a_start, b_start) + 1
    return intersect / union


def find_entries_within_range(start_year: int, end_year: int, history: Dict = None) -> List[Dict]:
    """Return entries overlapping the given range with an overlap score.

    Each result is a dict: {"key": key, "entry": rec, "overlap": float}
    """
    if start_year > end_year:
        start_year, end_year = end_year, start_year
    h = history or load_history()
    results = []
    for key, records in h.items():
        record_list = []
        if isinstance(records, dict):
            for v in records.values():
                if isinstance(v, list):
                    record_list.extend(v)
        elif isinstance(records, list):
            record_list = records
        else:
            continue

        for rec in record_list:
            if not isinstance(rec, dict):
                continue
            s, e = _entry_year_range(rec)
            overlap = _overlap_fraction(start_year, end_year, s, e)
            if overlap > 0.0:
                results.append({'key': key, 'entry': rec, 'overlap': overlap, 'entry_start': s, 'entry_end': e})
    # sort by overlap descending then by entry span
    results.sort(key=lambda r: (-r['overlap'], (r['entry_end'] - r['entry_start'])))
    return results


def query_period_coverage(start_year: int, end_year: int, history: Dict = None) -> str:
    """Return a short human-friendly summary of matching historical entries for the period."""
    matches = find_entries_within_range(start_year, end_year, history)
    if not matches:
        return f"No recorded historical entries overlap {start_year} to {end_year}."
    lines = [f"Entries overlapping {start_year}–{end_year}:"]
    for m in matches[:10]:
        key = m['key']
        rec = m['entry']
        ov = round(m['overlap'] * 100, 1)
        start = m.get('entry_start')
        end = m.get('entry_end')
        lines.append(f"- {key} ({start}–{end}) — {ov}% overlap — {rec.get('gloss','')}")
    return '\n'.join(lines)


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser(description='Lookup historical entries by year or range.')
    p.add_argument('start', type=int, help='start year or single year')
    p.add_argument('end', type=int, nargs='?', help='end year (optional)')
    args = p.parse_args()
    if args.end is None:
        year = args.start
        matches = find_entries_covering_year(year)
        if not matches:
            print(f'No entries covering {year}.')
        else:
            for key, rec in matches:
                s, e = _entry_year_range(rec)
                print(f"{key}: {s}–{e} — {rec.get('gloss','')}")
    else:
        print(query_period_coverage(args.start, args.end))
