import os
import json
import uuid
from datetime import datetime
from typing import Dict, List

try:
    import taxonomic_grammar as tg
except Exception:
    tg = None

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), 'data', 'nerve_sessions')
os.makedirs(SESSIONS_DIR, exist_ok=True)


class NerveCenter:
    """Simple session manager that turns taxonomy results into a stateful "nerve".

    Responsibilities:
    - create/load/save sessions
    - maintain scored items and explored flags
    - provide top items, alerts, and expansion helpers
    """

    def __init__(self):
        self.sessions: Dict[str, Dict] = {}

    def _session_path(self, session_id: str) -> str:
        return os.path.join(SESSIONS_DIR, f"{session_id}.json")

    def create_session(self, taxonomy_result: Dict, session_id: str = None, meta: Dict = None) -> str:
        if session_id is None:
            session_id = uuid.uuid4().hex[:16]
        meta = meta or {}
        items = []
        # flatten taxons
        for frag in taxonomy_result.get('fragments', []):
            for t in frag.get('matches', []):
                item = t.copy()
                item['fragment'] = frag.get('fragment')
                item['keywords'] = frag.get('keywords', [])
                # compute score using taxonomic_grammar scoring if available
                if tg and hasattr(tg, '_score_taxon'):
                    item['score'] = tg._score_taxon(item)
                else:
                    item['score'] = 1
                item['explored'] = False
                items.append(item)

        # sort descending by score
        items.sort(key=lambda x: x.get('score', 0), reverse=True)
        session = {
            'id': session_id,
            'created': datetime.utcnow().isoformat() + 'Z',
            'meta': meta,
            'result': taxonomy_result,
            'items': items
        }
        self.sessions[session_id] = session
        self.save_session(session_id)
        return session_id

    def save_session(self, session_id: str):
        session = self.sessions.get(session_id)
        if not session:
            return
        path = self._session_path(session_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(session, f, indent=2, ensure_ascii=False)

    def load_session(self, session_id: str):
        path = self._session_path(session_id)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            session = json.load(f)
        self.sessions[session_id] = session
        return session

    def list_sessions(self) -> List[str]:
        return list(self.sessions.keys())

    def get_top_items(self, session_id: str, n: int = 5):
        s = self.sessions.get(session_id) or self.load_session(session_id)
        if not s:
            return []
        return s.get('items', [])[:n]

    def mark_explored(self, session_id: str, variable: str):
        s = self.sessions.get(session_id) or self.load_session(session_id)
        if not s:
            return False
        changed = False
        for it in s.get('items', []):
            if it.get('variable') == variable:
                it['explored'] = True
                changed = True
        if changed:
            self.save_session(session_id)
        return changed

    def expand_variable(self, session_id: str, variable: str, max_items: int = 6) -> str:
        """Return a friendly expansion for a given variable (genus).

        Uses `tg.render_response` on filtered taxons if available, otherwise returns raw items.
        """
        s = self.sessions.get(session_id) or self.load_session(session_id)
        if not s:
            return "session not found"
        items = [it for it in s.get('items', []) if it.get('variable') == variable]
        if not items:
            # fuzzy fallback: find items containing variable substring
            items = [it for it in s.get('items', []) if variable in (it.get('variable') or '')]
        if not items:
            return "no items for variable"
        # Mark as explored
        for it in items:
            it['explored'] = True
        self.save_session(session_id)

        if tg and hasattr(tg, '_render_from_taxons'):
            return tg._render_from_taxons(items, positivity=True)
        if tg and hasattr(tg, 'render_response'):
            # build a temporary result
            temp = {'prompt': s.get('result', {}).get('prompt', ''), 'fragments': [{'fragment': it.get('fragment'), 'keywords': it.get('keywords', []), 'matches': [it]} for it in items]}
            return tg.render_response(temp, max_items=max_items, positivity=True)

        # fallback raw
        out_lines = []
        for it in items[:max_items]:
            out_lines.append(f"{it.get('variable')} ({it.get('phylum')}): {it.get('value')}")
        return "\n".join(out_lines)

    def chain_from_variable(self, session_id: str, variable: str, steps: int = 6):
        """Create chained conjecture options focused on the same family/phylum as `variable`.

        Marks `variable` explored, gathers related items (same family or phylum),
        and returns structured options like `conjecture_sinewave` (list of dicts with `variable` and `text`).
        """
        # mark explored
        self.mark_explored(session_id, variable)

        s = self.sessions.get(session_id) or self.load_session(session_id)
        if not s:
            return [{'variable': None, 'text': 'session not found'}]

        # find reference
        ref = None
        for it in s.get('items', []):
            if it.get('variable') == variable:
                ref = it
                break
        if not ref:
            return [{'variable': None, 'text': 'variable not found in session'}]

        # gather related items in same family first, then same phylum
        family = ref.get('family')
        phylum = ref.get('phylum')
        related = [it for it in s.get('items', []) if it.get('family') == family and it.get('variable') != variable]
        if not related:
            related = [it for it in s.get('items', []) if it.get('phylum') == phylum and it.get('variable') != variable]
        if not related:
            # fallback to siblings by variable substring
            related = [it for it in s.get('items', []) if variable in (it.get('variable') or '') and it.get('variable') != variable]

        if not related:
            return [{'variable': None, 'text': 'no related items found for chaining'}]

        # build temp_result and reuse taxonomic_grammar.generate_variations if available
        temp_result = {'prompt': s.get('result', {}).get('prompt', ''), 'fragments': []}
        for it in related:
            temp_result['fragments'].append({'fragment': it.get('fragment'), 'keywords': it.get('keywords', []), 'matches': [it]})

        try:
            import taxonomic_grammar as tg
            # prefer concise conditional variations when available (supports reverse traversal)
            if hasattr(tg, 'generate_variations_conditional'):
                texts = tg.generate_variations_conditional(temp_result, steps=steps, positivity=True, minimal=True, reverse=True)
            elif hasattr(tg, 'generate_poetic_variations'):
                texts = tg.generate_poetic_variations(temp_result, steps=steps, positivity=True, reverse=True)
            elif hasattr(tg, 'generate_variations'):
                texts = tg.generate_variations(temp_result, steps=steps, positivity=True)
                options = []
                for i, txt in enumerate(texts):
                    var = related[i % len(related)].get('variable')
                    options.append({'variable': var, 'text': txt})
                return options
            if hasattr(tg, '_render_from_taxons'):
                out = []
                for i in range(steps):
                    idx = i % len(related)
                    out.append({'variable': related[idx].get('variable'), 'text': tg._render_from_taxons([related[idx]], positivity=True)})
                return out
        except Exception:
            pass

        # fallback simple options
        opts = []
        for i in range(min(steps, len(related))):
            it = related[i]
            opts.append({'variable': it.get('variable'), 'text': f"Explore {it.get('variable')} ({it.get('family')})"})
        return opts

    def get_lineage(self, session_id: str, variable: str) -> dict:
        """Return the taxonomy lineage for `variable` in session: kingdom, phylum, family, order.

        If the variable isn't found, return an empty dict.
        """
        s = self.sessions.get(session_id) or self.load_session(session_id)
        if not s:
            return {}
        for it in s.get('items', []):
            if it.get('variable') == variable:
                # return the immediate taxonomy fields
                return {
                    'kingdom': it.get('kingdom'),
                    'phylum': it.get('phylum'),
                    'family': it.get('family'),
                    'order': it.get('order'),
                    'variable': it.get('variable'),
                    'type': it.get('type'),
                    'value': it.get('value')
                }
        return {}

    def list_below(self, session_id: str, variable: str, scope: str = 'family', limit: int = 20) -> list:
        """List items 'below' a taxonomy node for `variable`.

        scope: 'family' or 'phylum' or 'kingdom'.
        Returns list of items (dict) within the same scope (excluding the variable itself).
        """
        s = self.sessions.get(session_id) or self.load_session(session_id)
        if not s:
            return []
        # find the reference item
        ref = None
        for it in s.get('items', []):
            if it.get('variable') == variable:
                ref = it
                break
        if not ref:
            # fuzzy fallback: find item that contains variable substring
            for it in s.get('items', []):
                if variable in (it.get('variable') or ''):
                    ref = it
                    break
        if not ref:
            return []

        key = scope if scope in ('family','phylum','kingdom') else 'family'
        ref_val = ref.get(key)
        if not ref_val:
            return []
        out = [it for it in s.get('items', []) if it.get(key) == ref_val and it.get('variable') != variable]
        # sort by score desc
        out.sort(key=lambda x: x.get('score',0), reverse=True)
        return out[:limit]

    def alerts(self, session_id: str, threshold: int = 5):
        s = self.sessions.get(session_id) or self.load_session(session_id)
        if not s:
            return []
        return [it for it in s.get('items', []) if (it.get('score', 0) >= threshold and not it.get('explored'))]

    def conjecture_sinewave(self, session_id: str, steps: int = 6) -> list:
        """Produce a set of conjectural variation prompts using a cosine-wave over the deepest taxa.

        Returns a list of rendered variation strings (one per step). Uses `taxonomic_grammar.generate_variations`
        when available by building a focused temporary result consisting of the deepest items.
        """
        s = self.sessions.get(session_id) or self.load_session(session_id)
        if not s:
            return ["session not found"]

        items = s.get('items', [])
        if not items:
            return ["no items in session"]

        # Depth heuristic: prefer non-general families and longer 'order' (more detailed gloss)
        def depth_metric(it):
            depth = 0
            if it.get('family') and it.get('family') != 'general':
                depth += 3
            ordtxt = it.get('order') or ''
            depth += min(10, len(str(ordtxt)) // 50)
            # value length also indicates depth
            val = it.get('value') or ''
            depth += min(10, len(str(val)) // 80)
            return depth

        items_sorted = sorted(items, key=lambda x: (depth_metric(x), x.get('score', 0)), reverse=True)

        # pick up to steps*2 candidates but keep unique variables
        vars_seen = set()
        selected = []
        for it in items_sorted:
            v = it.get('variable')
            if not v or v in vars_seen:
                continue
            vars_seen.add(v)
            selected.append(it)
            if len(selected) >= max(3, steps * 2):
                break

        # Build a temporary result for generate_variations to operate on
        temp_result = {'prompt': s.get('result', {}).get('prompt', ''), 'fragments': []}
        for it in selected:
            temp_result['fragments'].append({'fragment': it.get('fragment'), 'keywords': it.get('keywords', []), 'matches': [it]})

        options = []
        # If taxonomic_grammar available, use its generator; else fallback to rendering each item
        try:
            import taxonomic_grammar as tg
            if hasattr(tg, 'generate_variations'):
                texts = tg.generate_variations(temp_result, steps=steps, positivity=True)
                # Attempt to pair generated texts with selected variables in sampling order
                # If lengths differ, pair as many as possible.
                for i, txt in enumerate(texts):
                    var = selected[i % len(selected)].get('variable')
                    options.append({'variable': var, 'text': txt})
                return options
            # fallback: use internal render helper if present
            if hasattr(tg, '_render_from_taxons'):
                for i in range(steps):
                    # use cosine mapping for fallback selection as well
                    phase = 2 * __import__('math').pi * (i / max(1, steps))
                    s_val = __import__('math').cos(phase)
                    idx = int(round(((s_val + 1) / 2) * (len(selected) - 1)))
                    txt = tg._render_from_taxons([selected[idx]], positivity=True)
                    options.append({'variable': selected[idx].get('variable'), 'text': txt})
                return options
        except Exception:
            pass

        # Simple fallback: create short conjectural option structures
        for i in range(steps):
            it = selected[i % len(selected)]
            v = it.get('variable')
            fam = it.get('family')
            summary = str(it.get('value') or '').strip()
            line = f"Option {i+1}: Explore '{v}' ({fam}) — {summary[:240]}"
            options.append({'variable': v, 'text': line})
        return options

    def conjecture_paragraph(self, session_id: str, steps: int = 6) -> str:
        """Build a single inviting paragraph that nests short sentences for each conjecture option.

        Uses the same selection heuristic as `conjecture_sinewave` and returns a single paragraph
        where each sentence briefly describes an option and invites the user to choose or ask their own.
        """
        # reuse the selection logic from conjecture_sinewave
        s = self.sessions.get(session_id) or self.load_session(session_id)
        if not s:
            return "session not found"

        items = s.get('items', [])
        if not items:
            return "no items in session"

        def depth_metric(it):
            depth = 0
            if it.get('family') and it.get('family') != 'general':
                depth += 3
            ordtxt = it.get('order') or ''
            depth += min(10, len(str(ordtxt)) // 50)
            val = it.get('value') or ''
            depth += min(10, len(str(val)) // 80)
            return depth

        items_sorted = sorted(items, key=lambda x: (depth_metric(x), x.get('score', 0)), reverse=True)

        vars_seen = set()
        selected = []
        for it in items_sorted:
            v = it.get('variable')
            if not v or v in vars_seen:
                continue
            vars_seen.add(v)
            selected.append(it)
            if len(selected) >= max(3, steps * 2):
                break

        if not selected:
            return "no suitable conjectures"

        # build sentences: keep them short and inviting
        sentences = []
        for i in range(min(steps, len(selected))):
            it = selected[i]
            v = it.get('variable') or 'this topic'
            fam = it.get('family') or ''
            fam_part = f" ({fam})" if fam else ''
            # short summary from value or order
            summary = (it.get('value') or it.get('order') or '').strip()
            if not summary:
                summary = 'a related concept worth exploring.'
            # take first sentence-like chunk
            summary = summary.split('.\n')[0].split('.')[0]
            summary = summary.strip()
            if len(summary) > 180:
                summary = summary[:177].rstrip() + '...'
            sentence = f"Option {i+1}: explore '{v}'{fam_part} — {summary}."
            sentences.append(sentence)

        # combine into a nested paragraph
        paragraph = ' '.join(sentences)
        paragraph += ' Which direction would you like to explore? You can pick an option number, ask for more detail on any option, or propose your own direction.'
        return paragraph


nerve = NerveCenter()

if __name__ == '__main__':
    print('nerve_center module — import and use NerveCenter. Sessions stored in', SESSIONS_DIR)
