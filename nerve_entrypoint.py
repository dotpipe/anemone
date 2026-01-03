"""Interactive entrypoint for the Nerve Center.

Usage:
  python nerve_entrypoint.py        # interactive loop

Commands (typed at the prompt):
  new <prompt>            Create a new session from <prompt>
  append <sid> <prompt>   Create a new child session linked to <sid>
  top <sid> [n]           Show top n items for session
  expand <sid> <variable> Expand a genus/variable in session
  variations <sid> [n]    Show variations (sine-wave traversal) for session
  list                    List known session ids
  load <sid>              Load session and show brief summary
  exit                   Quit

This file exposes `create_session_from_prompt(prompt)` for non-interactive use.
"""

import sys
import json
from typing import Optional
import os

try:
    import taxonomic_grammar as tg
except Exception:
    tg = None

try:
    from nerve_center import nerve
except Exception:
    nerve = None

# Settings file for Anemone interactive shell
DEFAULT_SETTINGS = {
    'style': 'minimal',        # 'minimal' | 'poetic' | 'compact'
    'reverse': True,          # traverse reverse-taxonomy by default
    'minimal_templates': True, # use minimal template words
    'variations_steps': 6,
    'positivity': True,
    'use_local_generators': True
}
DEFAULT_SETTINGS.update({
    'anchor_level': 'phylum',   # 'kingdom' | 'phylum' | 'none'
    'temperature': 0.2,         # 0.0..1.0, higher => more creative
    'verbosity': 'long'         # 'short' | 'long'
})
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), 'data', 'anemone_settings.json')


def load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                s = json.load(f)
            # merge defaults
            out = DEFAULT_SETTINGS.copy()
            out.update(s or {})
            return out
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_settings(s):
    try:
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(s, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def create_session_from_prompt(prompt: str, parent: Optional[str] = None) -> Optional[str]:
    """Create a nerve session from `prompt`. Returns session id or None."""
    if tg is None or nerve is None:
        print('Required modules not available (taxonomic_grammar and nerve_center).')
        return None
    result = tg.analyze(prompt)
    meta = {'parent': parent} if parent else {}
    sid = nerve.create_session(result, meta=meta)
    # print friendly summary
    if hasattr(tg, 'render_response'):
        print('\n--- Summary ---')
        print(tg.render_response(result, max_items=6, positivity=True))
    return sid


def interactive():
    print('Nerve Center interactive. Type "help" for commands.')
    cur = None
    settings = load_settings()
    while True:
        try:
            line = input('nerve> ').strip()
        except (EOFError, KeyboardInterrupt):
            print('\nexiting')
            return
        if not line:
            continue
        parts = line.split(' ', 2)
        cmd = parts[0].lower()
        if cmd in ('quit', 'exit'):
            print('bye')
            return
        if cmd == 'help':
            print(__doc__)
            continue
        if cmd == 'new':
            if len(parts) < 2:
                print('usage: new <prompt>')
                continue
            prompt = line[len('new '):]
            sid = create_session_from_prompt(prompt)
            if sid:
                print('created', sid)
                cur = sid
            continue
        if cmd == 'settings':
            # show current settings
            print(json.dumps(settings, indent=2, ensure_ascii=False))
            continue
        if cmd == 'toggle':
            # toggle <key>
            if len(parts) < 2:
                print('usage: toggle <key>')
                continue
            key = parts[1]
            if key not in settings:
                print('unknown setting')
                continue
            val = settings.get(key)
            if isinstance(val, bool):
                settings[key] = not val
                save_settings(settings)
                print(f"{key} -> {settings[key]}")
            else:
                print('setting is not boolean; use set <key> <value>')
            continue
        if cmd == 'set':
            # set <key> <value>
            if len(parts) < 3:
                print('usage: set <key> <value>')
                continue
            key = parts[1]
            val = parts[2]
            if key not in settings:
                print('unknown setting')
                continue
            # try to coerce types
            curv = settings.get(key)
            if isinstance(curv, bool):
                settings[key] = val.lower() in ('1','true','yes','y')
            elif isinstance(curv, int):
                try:
                    settings[key] = int(val)
                except Exception:
                    print('invalid int')
                    continue
            else:
                settings[key] = val
            save_settings(settings)
            print(f"{key} -> {settings[key]}")
            continue
        if cmd == 'reset-settings':
            settings = DEFAULT_SETTINGS.copy()
            save_settings(settings)
            print('settings reset to defaults')
            continue
        if cmd == 'append':
            if len(parts) < 3:
                print('usage: append <sid> <prompt>')
                continue
            sid = parts[1]
            prompt = parts[2]
            child = create_session_from_prompt(prompt, parent=sid)
            if child:
                print('created child session', child)
            continue
        if cmd == 'list':
            ids = list(nerve.sessions.keys())
            # include on-disk sessions
            print('\n'.join(ids))
            continue
        if cmd == 'top':
            if len(parts) < 2:
                print('usage: top <sid> [n]')
                continue
            sid = parts[1]
            n = 5
            if len(parts) >= 3:
                try:
                    n = int(parts[2])
                except Exception:
                    pass
            tops = nerve.get_top_items(sid, n=n)
            print(json.dumps(tops, indent=2, ensure_ascii=False))
            continue
        if cmd == 'expand':
            if len(parts) < 3:
                print('usage: expand <sid> <variable>')
                continue
            sid = parts[1]
            variable = parts[2]
            out = nerve.expand_variable(sid, variable)
            print(out)
            continue
        if cmd == 'variations':
            if len(parts) < 2:
                print('usage: variations <sid> [n]')
                continue
            sid = parts[1]
            n = settings.get('variations_steps', 6)
            if len(parts) >= 3:
                try:
                    n = int(parts[2])
                except Exception:
                    pass
            s = nerve.sessions.get(sid) or nerve.load_session(sid)
            if not s:
                print('session not found')
                continue
            # pick generator based on settings
            if tg:
                style = settings.get('style', 'minimal')
                if style == 'minimal' and hasattr(tg, 'generate_variations_conditional'):
                    vars_out = tg.generate_variations_conditional(s.get('result', {}), steps=n, positivity=settings.get('positivity', True), minimal=settings.get('minimal_templates', True), reverse=settings.get('reverse', True))
                elif style == 'poetic' and hasattr(tg, 'generate_poetic_variations'):
                    vars_out = tg.generate_poetic_variations(s.get('result', {}), steps=n, positivity=settings.get('positivity', True), reverse=settings.get('reverse', True))
                else:
                    vars_out = tg.generate_variations(s.get('result', {}), steps=n, positivity=settings.get('positivity', True))
                for v in vars_out:
                    print('\n' + v)
            else:
                print('variations generator unavailable')
            continue
        if cmd == 'conjecture':
            if len(parts) < 2:
                print('usage: conjecture <sid> [n]')
                continue
            sid = parts[1]
            n = 6
            if len(parts) >= 3:
                try:
                    n = int(parts[2])
                except Exception:
                    pass
            if not nerve:
                print('nerve_center not available')
                continue
            conj = nerve.conjecture_sinewave(sid, steps=n)
            print('\n--- Sine-wave conjectures (choose a direction or ask your own) ---')
            # conj is a list of {'variable', 'text'}
            # If local generators preferred, regenerate texts according to settings
            if settings.get('use_local_generators', True) and tg:
                # build a temp_result from conj variables
                vars_list = [c.get('variable') if isinstance(c, dict) else None for c in conj]
                temp_result = {'prompt': nerve.sessions.get(sid, {}).get('result', {}).get('prompt',''), 'fragments': []}
                for v, citem in zip(vars_list, conj):
                    if v:
                        # find item in session
                        s = nerve.sessions.get(sid) or nerve.load_session(sid)
                        found = None
                        for it in s.get('items', []):
                            if it.get('variable') == v:
                                found = it
                                break
                        if found:
                            temp_result['fragments'].append({'fragment': found.get('fragment'), 'keywords': found.get('keywords', []), 'matches': [found]})
                style = settings.get('style', 'minimal')
                if style == 'minimal' and hasattr(tg, 'generate_variations_conditional'):
                    texts = tg.generate_variations_conditional(temp_result, steps=n, positivity=settings.get('positivity', True), minimal=settings.get('minimal_templates', True), reverse=settings.get('reverse', True), anchor_level=settings.get('anchor_level','phylum'), temperature=settings.get('temperature',0.2), verbosity=settings.get('verbosity','long'))
                elif style == 'poetic' and hasattr(tg, 'generate_poetic_variations'):
                    texts = tg.generate_poetic_variations(temp_result, steps=n, positivity=settings.get('positivity', True), reverse=settings.get('reverse', True))
                else:
                    texts = tg.generate_variations(temp_result, steps=n, positivity=settings.get('positivity', True))
                # pair texts back to conj list
                new_conj = []
                for i, c in enumerate(conj):
                    var = c.get('variable') if isinstance(c, dict) else None
                    txt = texts[i] if i < len(texts) else (c.get('text') if isinstance(c, dict) else str(c))
                    new_conj.append({'variable': var, 'text': txt})
                conj = new_conj
            # print options
            for i, c in enumerate(conj, 1):
                # support either dict items or simple string fallbacks
                if isinstance(c, dict):
                    txt = c.get('text')
                else:
                    txt = str(c)
                print(f"{i}. {txt}\n")
            # also print an inviting paragraph combining the options
            if hasattr(nerve, 'conjecture_paragraph'):
                para = nerve.conjecture_paragraph(sid, steps=n)
                print('\n--- Invitation Paragraph ---')
                print(para)

            # prompt for a selection immediately in interactive mode
            if True:
                try:
                    sel = input('Pick an option number to expand (or press Enter to skip): ').strip()
                except (EOFError, KeyboardInterrupt):
                    sel = ''
                if sel.isdigit():
                    idx = int(sel) - 1
                    if 0 <= idx < len(conj):
                        chosen = conj[idx]
                        if isinstance(chosen, dict):
                            var = chosen.get('variable')
                            print('\n--- Expansion for chosen option ---')
                            print(nerve.expand_variable(sid, var))
                        else:
                            # simple string option; just print it
                            print('\n--- Option ---')
                            print(str(chosen))
                        # offer chaining
                        try:
                            chain_ask = input('Chain deeper from this option? (y/N): ').strip().lower()
                        except (EOFError, KeyboardInterrupt):
                            chain_ask = 'n'
                        if chain_ask == 'y':
                            # perform chaining loop
                            cur_options = nerve.chain_from_variable(sid, var, steps=n)
                            while cur_options:
                                print('\n--- Chained options ---')
                                for j, co in enumerate(cur_options, 1):
                                    if isinstance(co, dict):
                                        ctxt = co.get('text')
                                    else:
                                        ctxt = str(co)
                                    print(f"{j}. {ctxt}\n")
                                try:
                                    sel2 = input('Pick an option number to expand (or Enter to stop chaining): ').strip()
                                except (EOFError, KeyboardInterrupt):
                                    sel2 = ''
                                if sel2.isdigit():
                                    idx2 = int(sel2) - 1
                                    if 0 <= idx2 < len(cur_options):
                                        chosen2 = cur_options[idx2]
                                        if isinstance(chosen2, dict):
                                            v2 = chosen2.get('variable')
                                            print('\n--- Expansion for chained option ---')
                                            print(nerve.expand_variable(sid, v2))
                                            # continue loop by deriving new chain from v2
                                            cur_options = nerve.chain_from_variable(sid, v2, steps=n)
                                            continue
                                        else:
                                            print('\n--- Option ---')
                                            print(str(chosen2))
                                            break
                                break
                else:
                    # user skipped or entered non-digit
                    pass
            continue
        if cmd == 'up':
            if len(parts) < 3:
                print('usage: up <sid> <variable>')
                continue
            sid = parts[1]
            var = parts[2]
            if not nerve:
                print('nerve_center not available')
                continue
            lin = nerve.get_lineage(sid, var)
            if not lin:
                print('not found')
            else:
                print(json.dumps(lin, indent=2, ensure_ascii=False))
            continue
        if cmd in ('listbelow','below','siblings'):
            if len(parts) < 3:
                print('usage: listbelow <sid> <variable> [scope]')
                continue
            sid = parts[1]
            var = parts[2]
            scope = 'family'
            if len(parts) >= 4:
                scope = parts[3]
            out = nerve.list_below(sid, var, scope=scope)
            print(json.dumps(out, indent=2, ensure_ascii=False))
            continue
        if cmd == 'load':
            if len(parts) < 2:
                print('usage: load <sid>')
                continue
            sid = parts[1]
            s = nerve.load_session(sid)
            if not s:
                print('not found')
                continue
            print('loaded', sid)
            cur = sid
            continue
        print('unknown command; type help')


def main():
    if len(sys.argv) > 1:
        # simple script mode: create session
        prompt = ' '.join(sys.argv[1:])
        sid = create_session_from_prompt(prompt)
        if sid:
            print(sid)
        return
    interactive()


if __name__ == '__main__':
    main()
