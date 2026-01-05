"""Small integration helpers connecting the engine to the patcher CLI functions.

Provide `patch_kingdom_json_integration` for callers that want to apply or preview
patches to kingdom JSON files from within the engine.
This module also provides a tiny file-backed pending-patch store so the engine
can persist pending previewed patch intents across sessions.
"""
from __future__ import annotations
from typing import Dict
import json
import uuid
from datetime import datetime
from pathlib import Path

# pending patches file (workspace-relative)
_PENDING_PATH = Path('data') / 'pending_patches.json'


def _ensure_pending_store():
    _PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not _PENDING_PATH.exists():
        _PENDING_PATH.write_text('[]', encoding='utf-8')


def load_pending_patches() -> list:
    _ensure_pending_store()
    try:
        return json.loads(_PENDING_PATH.read_text(encoding='utf-8'))
    except Exception:
        return []


def save_pending_patches(entries: list) -> None:
    _ensure_pending_store()
    _PENDING_PATH.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding='utf-8')


def add_pending_patch(parsed: dict) -> str:
    """Add a parsed patch intent to the pending store and return a generated id."""
    entries = load_pending_patches()
    pid = str(uuid.uuid4())
    entry = {
        'id': pid,
        'parsed': parsed,
        'created_at': datetime.utcnow().isoformat() + 'Z',
    }
    entries.append(entry)
    save_pending_patches(entries)
    return pid


def get_pending_patch(pid: str) -> dict | None:
    entries = load_pending_patches()
    for e in entries:
        if e.get('id') == pid:
            return e
    return None


def remove_pending_patch(pid: str) -> bool:
    entries = load_pending_patches()
    new = [e for e in entries if e.get('id') != pid]
    if len(new) == len(entries):
        return False
    save_pending_patches(new)
    return True


def patch_kingdom_json_integration(path: str, grep: str, replace: str = '', regex: bool = False, layer: str | None = None, *, interactive: bool = False, inplace: bool = False, out: str | None = None, dry_run: bool = False) -> Dict:
    """Integration wrapper to apply or preview patches to a kingdom JSON file.

    Returns a summary dict: {'planned': [...], 'applied': int, 'written_to': path|None}
    """
    try:
        from scripts.patch_kingdom_json import load_json, write_json, apply_action_changes
    except Exception as e:
        raise RuntimeError('patcher module not available: ' + str(e))

    obj = load_json(path)
    layers = obj.get('layers', [])

    # scan for proposed changes
    _, details = apply_action_changes(layers, grep, replace, regex, layer, apply=False)
    summary = {'planned': details, 'applied': 0, 'written_to': None}
    if not details:
        return summary

    if interactive:
        for i, (lname, pi, li, old, new) in enumerate(details, 1):
            resp = input(f'Apply change [{i}] Layer={lname} para={pi} line={li}? (Y/n) ').strip().lower()
            if resp in ('', 'y'):
                target = next((L for L in layers if L.get('name') == lname), None)
                if target:
                    target['actions'][pi][li] = new
                    summary['applied'] += 1
    else:
        if dry_run:
            return summary
        applied_count, _ = apply_action_changes(layers, grep, replace, regex, layer, apply=True)
        summary['applied'] = applied_count

    if summary['applied'] > 0:
        if inplace:
            from pathlib import Path
            p = Path(path)
            bak = p.with_suffix(p.suffix + '.bak')
            p.replace(bak)
            write_json(str(p), obj)
            summary['written_to'] = str(p)
        elif out:
            write_json(out, obj)
            summary['written_to'] = out

    # audit the operation
    try:
        from scripts.patch_logger import audit
        audit('apply' if summary.get('applied', 0) > 0 else 'preview', None, {
            'path': path,
            'grep': grep,
            'replace': replace,
            'layer': layer,
            'planned': len(summary.get('planned', [])),
            'applied': summary.get('applied', 0),
            'written_to': summary.get('written_to'),
        })
    except Exception:
        pass

    return summary


def patch_kingdom_json_chat(path: str, grep: str, replace: str = '', regex: bool = False, layer: str | None = None, apply: bool = False, inplace: bool = False, out: str | None = None, dry_run: bool = False, limit: int = 20) -> str:
    """Chat-friendly wrapper returning human-readable report.

    - If `apply` is False: returns a preview of planned changes (up to `limit`).
    - If `apply` is True: performs the changes (respecting dry_run/inplace/out) and returns a summary.
    """
    summary = patch_kingdom_json_integration(path, grep, replace, regex, layer, interactive=False, inplace=inplace, out=out, dry_run=dry_run)
    planned = summary.get('planned', [])
    if not planned:
        return 'No matches found.'

    if not apply:
        lines = [f'Planned replacements: {len(planned)} (showing up to {limit})']
        for i, (lname, pi, li, old, new) in enumerate(planned[:limit], 1):
            lines.append(f'[{i}] Layer={lname} para={pi} line={li}')
            lines.append(f'    - {old}')
            lines.append(f'    + {new}')
            # try to show git blame for the line in the JSON file
            try:
                nums = find_line_numbers(path, old)
                if nums:
                    b = get_git_blame_for_lines(path, nums[0], nums[0])
                    if b:
                        lines.append(f'    blame: {b.strip()}')
            except Exception:
                pass
        if len(planned) > limit:
            lines.append(f'... and {len(planned)-limit} more changes')
        lines.append('\nTo apply: call with apply=True (and optionally --inplace).')
        return '\n'.join(lines)

    # apply=True path
    applied = summary.get('applied', 0)
    written = summary.get('written_to')
    out_lines = [f'Applied {applied} changes.']
    if written:
        out_lines.append(f'Wrote patched file to: {written}')
    else:
        out_lines.append('No file was written (use inplace or out to persist changes).')
    return '\n'.join(out_lines)


def detect_and_run_patch_from_prompt(prompt: str, default_path: str = 'data/generated_kingdoms.json') -> str | None:
    """Detect patch intent in a natural-language `prompt` and run preview/apply.

    Returns a human-readable string if a patch intent was detected and executed,
    otherwise returns None.
    """
    import re
    p = prompt.strip()
    lower = p.lower()
    # quick intent check
    if 'patch' not in lower and 'replace' not in lower and 'change' not in lower and 'rename' not in lower:
        return None

    # reuse detect_patch_intent for parsing (expanded patterns)
    parsed = detect_patch_intent(p, default_path=default_path)
    if not parsed:
        return 'I detected a request to patch, but couldn\'t parse "replace OLD with NEW" or similar. Try: replace "OLD" with "NEW", or say: change OLD to NEW.'

    # If user explicitly asked to apply, run and return result; otherwise save pending and return preview
    try:
        if parsed.get('apply_flag'):
            return patch_kingdom_json_chat(parsed.get('path', default_path), parsed['old'], parsed['new'], regex=parsed.get('regex_flag', False), layer=parsed.get('layer'), apply=True, inplace=parsed.get('apply_flag'), out=None, dry_run=parsed.get('dry_run', False))

        # preview mode: get human-friendly preview and persist the intent as pending
        preview = patch_kingdom_json_chat(parsed.get('path', default_path), parsed['old'], parsed['new'], regex=parsed.get('regex_flag', False), layer=parsed.get('layer'), apply=False, inplace=False, out=None, dry_run=True)
        pid = add_pending_patch(parsed)
        return f"Preview saved as pending id {pid}.\n\n{preview}\n\nTo apply this pending patch later, say: apply {pid} (or 'apply pending {pid}')."
    except Exception as e:
        return f'Error running patch: {e}'


def detect_patch_intent(prompt: str, default_path: str = 'data/generated_kingdoms.json') -> dict | None:
    """Parse a natural-language prompt for patch intent and return a dict of parsed options.

    Returns None if no patch intent detected. Dict keys: old, new, apply_flag, dry_run, regex_flag, layer, path
    """
    import re
    p = prompt.strip()
    lower = p.lower()
    if 'patch' not in lower and 'replace' not in lower and 'change' not in lower:
        return None

    # try common phrasings
    patterns = [
        r"replace\s+['\"]?(?P<old>[^'\"]+)['\"]?\s+with\s+['\"]?(?P<new>[^'\"]+)['\"]?",
        r"grep\s+['\"]?(?P<old>[^'\"]+)['\"]?.*replace\s+['\"]?(?P<new>[^'\"]+)['\"]?",
        r"change\s+['\"]?(?P<old>[^'\"]+)['\"]?\s+(?:to|into)\s+['\"]?(?P<new>[^'\"]+)['\"]?",
        r"rename\s+['\"]?(?P<old>[^'\"]+)['\"]?\s+(?:to|into|as)\s+['\"]?(?P<new>[^'\"]+)['\"]?",
        r"(?P<old>[^\s]+)\s*->\s*(?P<new>[^\n]+)",
        r"(?P<old>[^\s]+)\s*=>\s*(?P<new>[^\n]+)",
    ]
    m = None
    for pat in patterns:
        m = re.search(pat, p, re.I)
        if m:
            break
    if not m:
        # try a more permissive 'OLD to NEW' without keywords
        m = re.search(r"['\"]?(?P<old>[^'\"]+)['\"]?\s+(?:to|into)\s+['\"]?(?P<new>[^'\"]+)['\"]?", p, re.I)
    if not m:
        return None

    old = (m.group('old') or '').strip()
    new = (m.group('new') or '').strip()
    apply_flag = bool(re.search(r"\bapply\b|\bwrite\b|\binplace\b|\bcommit\b", p, re.I))
    dry_run = bool(re.search(r"\bdry[- ]?run\b|\bpreview\b", p, re.I))
    regex_flag = bool(re.search(r"\bregex\b", p, re.I))
    layer_m = re.search(r"\blayer\s*[:=]?\s*(?P<layer>\w+)\b", p, re.I)
    layer = layer_m.group('layer') if layer_m else None
    path_m = re.search(r"([\w\-./\\]+\.json)", p)
    path = path_m.group(1) if path_m else default_path

    return {
        'old': old,
        'new': new,
        'apply_flag': apply_flag,
        'dry_run': dry_run,
        'regex_flag': regex_flag,
        'layer': layer,
        'path': path,
    }


def find_line_numbers(path: str, text: str) -> list:
    """Return list of 1-based line numbers in file `path` where `text` occurs exactly.

    Falls back to substring match. Returns empty list if not found or file missing.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        return []
    nums = []
    target = text.strip()
    for i, ln in enumerate(lines, 1):
        if ln.rstrip('\n').strip() == target:
            nums.append(i)
    if nums:
        return nums
    # fallback: substring
    for i, ln in enumerate(lines, 1):
        if target in ln:
            nums.append(i)
    return nums


def get_git_blame_for_lines(path: str, start: int, end: int) -> str | None:
    """Run `git blame -L start,end -- path` and return combined output line(s), or None.

    Returns None if git isn't available or file isn't tracked.
    """
    import subprocess
    try:
        res = subprocess.run(['git', 'blame', f'-L{start},{end}', '--', path], capture_output=True, text=True, check=False)
    except Exception:
        return None
    if res.returncode != 0:
        return None
    return res.stdout.strip()


def prepare_patch_preview(path: str, old: str, new: str, regex: bool = False, layer: str | None = None):
    """Return the planned change details for a proposed patch (not applied).

    Returns list of tuples (layer, para_index, line_index, old_line, new_line).
    """
    try:
        from scripts.patch_kingdom_json import load_json, apply_action_changes
    except Exception:
        return []
    try:
        obj = load_json(path)
    except Exception:
        return []
    layers = obj.get('layers', [])
    _, details = apply_action_changes(layers, old, new, regex, layer, apply=False)
    return details


def apply_selected_changes(path: str, old: str, new: str, regex: bool = False, layer: str | None = None, selected_indices: list | None = None, inplace: bool = False, out: str | None = None, dry_run: bool = False):
    """Apply selected planned changes. If `selected_indices` is None, apply all.

    Returns dict: {'applied': int, 'written_to': path|None}
    """
    import copy
    try:
        from scripts.patch_kingdom_json import load_json, write_json, apply_action_changes
    except Exception as e:
        raise RuntimeError('patcher module not available: ' + str(e))

    obj = load_json(path)
    layers = obj.get('layers', [])
    # get planned details
    _, details = apply_action_changes(layers, old, new, regex, layer, apply=False)
    if not details:
        return {'applied': 0, 'written_to': None}

    # determine which to apply
    to_apply = []
    if selected_indices is None:
        to_apply = list(range(len(details)))
    else:
        to_apply = [i for i in selected_indices if 0 <= i < len(details)]

    # apply selected changes by mutating obj in-place
    applied = 0
    for idx in to_apply:
        lname, pi, li, old_line, new_line = details[idx]
        target = next((L for L in obj.get('layers', []) if L.get('name') == lname), None)
        if target:
            try:
                target['actions'][pi][li] = new_line
                applied += 1
            except Exception:
                continue

    if applied == 0 or dry_run:
        return {'applied': applied, 'written_to': None}

    if inplace:
        from pathlib import Path
        p = Path(path)
        bak = p.with_suffix(p.suffix + '.bak')
        p.replace(bak)
        write_json(str(p), obj)
        return {'applied': applied, 'written_to': str(p)}
    elif out:
        write_json(out, obj)
        return {'applied': applied, 'written_to': out}
    else:
        return {'applied': applied, 'written_to': None}


def get_diff_for_change(path: str, detail) -> str:
    """Return a unified diff string for a single planned change detail.

    `detail` is a tuple (layer, para_index, line_index, old_line, new_line).
    """
    import difflib
    layer, pi, li, old_line, new_line = detail
    try:
        with open(path, 'r', encoding='utf-8') as f:
            orig_lines = f.readlines()
    except Exception:
        return 'Cannot read file for diff.'

    # find line numbers matching old_line
    nums = find_line_numbers(path, old_line)
    if not nums:
        # fallback: no exact match; show contextless change
        return '\n'.join(['- ' + old_line, '+ ' + new_line])

    # apply change to a copy of lines
    mod_lines = list(orig_lines)
    # use first matching occurrence
    lineno = nums[0] - 1
    mod_lines[lineno] = new_line + '\n'

    ud = difflib.unified_diff(orig_lines, mod_lines, fromfile=path, tofile=path + ' (modified)', lineterm='')
    return '\n'.join(list(ud))


def apply_pending_patch(pid: str, inplace: bool = True, out: str | None = None, dry_run: bool = False) -> dict:
    """Apply a pending patch identified by `pid`.

    Creates backups for any file that will be overwritten. Returns dict with
    keys: 'applied', 'written_to', 'error' (optional).
    """
    entry = get_pending_patch(pid)
    if not entry:
        return {'applied': 0, 'written_to': None, 'error': 'pending id not found'}

    parsed = entry.get('parsed') or {}
    path = parsed.get('path', 'data/generated_kingdoms.json')
    old = parsed.get('old', '')
    new = parsed.get('new', '')
    regex = parsed.get('regex_flag', False)
    layer = parsed.get('layer')
    dry = dry_run or parsed.get('dry_run', False)

    # If dry-run requested, return planned details without trying to read files
    if dry:
        try:
            details = prepare_patch_preview(path, old, new, regex, layer)
            return {'applied': 0, 'written_to': None, 'planned': len(details)}
        except Exception as e:
            return {'applied': 0, 'written_to': None, 'error': str(e)}

    # If writing to an 'out' path that exists, make a .bak copy first
    try:
        from shutil import copy2
        out_path = None
        if out:
            out_path = Path(out)
            if out_path.exists():
                copy2(str(out_path), str(out_path) + '.bak')

        # apply changes; apply_selected_changes will handle inplace backups
        res = apply_selected_changes(path, old, new, regex=regex, layer=layer, selected_indices=None, inplace=inplace, out=out, dry_run=dry)
        if res.get('applied', 0) > 0 and not dry:
            # remove pending entry after successful apply
            remove_pending_patch(pid)
        # audit
        try:
            from scripts.patch_logger import audit
            audit('apply_pending', None, {
                'pending_id': pid,
                'path': path,
                'applied': res.get('applied', 0),
                'written_to': res.get('written_to')
            })
        except Exception:
            pass
        return res
    except Exception as e:
        return {'applied': 0, 'written_to': None, 'error': str(e)}
