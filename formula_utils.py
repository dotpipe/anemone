"""Utilities to normalize and sanitize formula fragments for parsing.

Heuristics applied here are intentionally conservative but improve common
noisy fragments (e.g., convert `mc2` or `mc^2` -> `m*c**2`, replace
unicode multiplication signs, remove stray quotes, insert missing `*` between
number/identifier and parentheses, etc.).
"""
import re


SUPERSCRIPT_MAP = {
    '\u00b9': '1', '\u00b2': '2', '\u00b3': '3',
    '\u2070': '0', '\u2074': '4', '\u2075': '5', '\u2076': '6', '\u2077': '7', '\u2078': '8', '\u2079': '9'
}

# common unicode math symbol -> ascii / sympy-friendly mapping
UNICODE_MATH_MAP = {
    'π': 'pi', 'Π': 'pi',
    'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'Δ': 'Delta', 'ε': 'epsilon',
    'μ': 'mu', 'λ': 'lambda', 'σ': 'sigma', 'θ': 'theta', 'φ': 'phi',
    '×': '*', '·': '*', '•': '*', '÷': '/', '∕': '/', '⁄': '/',
    '±': '+-', '∓': '-+',
    '≤': '<=', '≥': '>=', '≠': '!=', '≈': '~=',
    '√': 'sqrt', '∑': 'sum', '∏': 'prod', '∫': 'Integral', '∂': 'd',
}


def replace_superscripts(s: str) -> str:
    if not s:
        return s
    for k, v in SUPERSCRIPT_MAP.items():
        s = s.replace(k, v)
    return s


def normalize_fragment(fragment: str) -> str:
    if not fragment:
        return ""
    s = fragment.strip()
    # remove enclosing quotes and stray trailing punctuation
    s = s.strip('"\'')
    s = s.strip('\n\r ')

    # quick rescues for common noisy fragments
    # replace '+=' artifacts (often from OCR/joined tokens) with '='
    s = s.replace('+=', '=')
    # if multiple '=' signs appear (a=b=c), prefer the last RHS as a recoverable expression
    if s.count('=') > 1:
        parts = s.split('=')
        s = parts[-1].strip()
    # collapse stray repeated punctuation at end
    s = re.sub(r"[\"']+$", "", s)

    # collapse repeated operator sequences (e.g. 'N=N+=N−' -> 'N=N=N-')
    s = re.sub(r'([=+\-*/]{2,})', lambda m: m.group(1)[0], s)

    # strip trailing parenthetical descriptors/dates: remove final '(...)'
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s)

    # remove trailing ' in <words>' descriptors when they look non-mathematical
    if re.search(r"\bin\b\s+[a-zA-Z]{3,}", s):
        # only strip if the trailing clause contains no digits or math operators
        m = re.search(r"\bin\b\s+(.+)$", s)
        if m and not re.search(r"[0-9=+\-*/()^]", m.group(1)):
            s = s[:m.start()].strip()

    # drop obvious date-like fragments (e.g., '1905/06') which are not math
    if re.search(r"\b\d{4}/\d{2}\b", s):
        return ""

    # drop chemical formula style fragments like 'CH=O' or 'C4H10' with '=' or '-' between element symbols
    nospace = s.replace(' ', '')
    if re.match(r"^[A-Z][A-Za-z0-9]*(?:[=\-][A-Z][A-Za-z0-9]*)+$", nospace):
        return ""

    # normalize unicode characters
    s = s.replace('–', '-').replace('\u2212', '-')
    s = replace_superscripts(s)

    # replace common unicode math symbols with sympy-friendly names
    for k, v in UNICODE_MATH_MAP.items():
        s = s.replace(k, v)

    # treat explicit colon ratio 'A:B' as division when standalone
    if re.match(r"^\s*[A-Za-z0-9_.]+\s*:\s*[A-Za-z0-9_.]+\s*$", s):
        s = re.sub(r"\s*:\s*", "/", s)

    # balance parentheses: remove excessive trailing ')' or add closing ')' if open remains
    open_paren = s.count('(')
    close_paren = s.count(')')
    if close_paren > open_paren:
        # remove trailing ')' characters until balanced
        while s.endswith(')') and s.count(')') > s.count('('):
            s = s[:-1]
    elif open_paren > close_paren:
        s = s + (')' * (open_paren - close_paren))

    # normalize common LaTeX caret to python exponent
    s = re.sub(r"\^\s*\{?\s*([0-9]+)\s*\}?", r"**\1", s)
    s = s.replace('^', '**')

    # handle simple LaTeX \frac{a}{b} -> (a)/(b)
    s = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"(\1)/(\2)", s)

    # map common LaTeX commands to ascii equivalents SymPy understands
    latex_map = {
        r"\\pi": "pi",
        r"\\theta": "theta",
        r"\\Delta": "Delta",
        r"\\delta": "delta",
        r"\\phi": "phi",
        r"\\lambda": "lambda",
        r"\\mu": "mu",
        r"\\sigma": "sigma",
        r"\\sin": "sin",
        r"\\cos": "cos",
        r"\\tan": "tan",
    }
    for k, v in latex_map.items():
        s = re.sub(k, v, s)

    # insert multiplication where implied: letters and digits, closing parenthesis
    # and identifier, number and identifier, etc. (avoid overly-greedy pattern
    # that turned `n(n+1)` into `n*n+1)`)
    s = re.sub(r"\b([A-Za-z])([A-Za-z])([0-9]+)\b", r"\1*\2**\3", s)
    s = re.sub(r"\b([A-Za-z])([0-9]+)\b", r"\1**\2", s)
    s = re.sub(r"\)\s*([A-Za-z0-9_])", r")*\1", s)
    s = re.sub(r"([0-9])\s*([A-Za-z])", r"\1*\2", s)

    # add * between number/identifier and opening parenthesis: 2(a+b) -> 2*(a+b)
    s = re.sub(r'(\d)\s*\(', r'\1*(', s)
    s = re.sub(r'([A-Za-z0-9_])\s*\(', r'\1*(', s)

    # remove multiple spaces
    s = re.sub(r'\s+', ' ', s)

    # trim again
    return s.strip()


def _is_number_literal(s: str) -> bool:
    try:
        float(s)
        return True
    except Exception:
        return False


def interpret_int_to_int(text: str) -> dict:
    """Interpret phrases like '(int) to (int)'.

    Returns a dict with keys:
      - `kind`: 'loop' or 'compare' or 'none'
      - `code`: a small Python code snippet implementing the intent
      - `a`, `b`: the captured endpoints (strings)

    Heuristics:
      - If the text contains the word 'compare', produce a comparison snippet.
      - Otherwise, produce a `for x in range(a, b+1):` loop using `x` as variable.
    """
    if not text:
        return {"kind": "none", "code": "", "a": None, "b": None}
    s = text.strip()
    low = s.lower()
    # pattern matches either numbers or identifiers possibly wrapped in parens
    m = re.search(r"\(?\s*([A-Za-z_][A-Za-z0-9_]*|\d+)\s*\)?\s+to\s+\(?\s*([A-Za-z_][A-Za-z0-9_]*|\d+)\s*\)?", s)
    if not m:
        return {"kind": "none", "code": "", "a": None, "b": None}
    a, b = m.group(1), m.group(2)
    is_compare = "compare" in low
    if is_compare:
        code = f"# compare {a} to {b}\nif {a} == {b}:\n    # TODO: handle equality\n    pass\nelse:\n    # TODO: handle inequality\n    pass"
        return {"kind": "compare", "code": code, "a": a, "b": b}
    # produce loop using x as loop variable
    # ensure numeric endpoints are left as-is; otherwise leave identifiers
    code = f"for x in range(int({a}), int({b})+1):\n    # TODO: body - break if condition met\n    if 2 * x == 1:\n        break"
    return {"kind": "loop", "code": code, "a": a, "b": b}


def interpret_prepositional_math(text: str) -> dict:
    """Interpret short English math phrases using prepositions.

    Returns a dict with keys:
      - kind: 'expr'|'loop'|'compare'|'none'
      - expr: a small Python expression string (if available)
      - code: a Python code snippet (fallback)
      - operands: list of captured operands
    """
    if not text:
        return {"kind": "none"}
    s = text.strip()
    low = s.lower()

    # direct equation detection: lhs = rhs, lhs := rhs, 'lhs equals rhs'
    m_eq = re.search(r"^\s*(.+?)\s*(?:=|:=|equals|≡)\s*(.+)\s*$", s)
    if m_eq:
        lhs = m_eq.group(1).strip()
        rhs = m_eq.group(2).strip()
        rhs_norm = normalize_fragment(rhs)
        return {"kind": "equation", "lhs": lhs, "rhs": rhs_norm}

    # ratio expressions: 'ratio of A to B', 'A:B', 'ratio A to B' -> interpret as (A)/(B)
    m = re.search(r"ratio(?:\s+of)?\s+([A-Za-z0-9_\.]+)\s+(?:to|:)\s+([A-Za-z0-9_\.]+)", low)
    if m:
        a, b = m.group(1), m.group(2)
        expr = f"({a})/({b})"
        return {"kind": "expr", "expr": expr, "operands": [a, b]}

    # explicit colon ratio like 'A:B' without the word 'ratio'
    m = re.search(r"\b([A-Za-z0-9_\.]+)\s*:\s*([A-Za-z0-9_\.]+)\b", low)
    if m and 'ratio' in low:
        a, b = m.group(1), m.group(2)
        expr = f"({a})/({b})"
        return {"kind": "expr", "expr": expr, "operands": [a, b]}

    # from/to or x to y -> range/loop
    m = re.search(r"(?:from\s+)?\(?\s*([A-Za-z0-9_+-]+)\s*\)?\s+to\s+\(?\s*([A-Za-z0-9_+-]+)\s*\)?", low)
    if m:
        a, b = m.group(1), m.group(2)
        is_compare = "compare" in low
        if is_compare:
            code = f"if {a} == {b}:\n    pass\nelse:\n    pass"
            return {"kind": "compare", "code": code, "operands": [a, b]}
        code = f"for x in range(int({a}), int({b})+1):\n    # body\n    if 2 * x == 1:\n        break"
        return {"kind": "loop", "code": code, "operands": [a, b]}

    # division patterns: 'X divided by Y' or 'X / Y'
    m = re.search(r"([A-Za-z0-9_\.]+)\s+(?:divided by|/|\/| per )\s+([A-Za-z0-9_\.]+)", low)
    if m:
        a, b = m.group(1), m.group(2)
        expr = f"({a})/({b})"
        return {"kind": "expr", "expr": expr, "operands": [a, b]}

    # handle 'gain' phrases commonly meaning ratio (output/input)
    # examples: 'gain of Vout to Vin', 'gain = Vout/Vin', 'voltage gain of 10 to 2'
    if 'gain' in low:
        m = re.search(r"gain(?:\s+of)?\s+([A-Za-z0-9_\.]+)\s+(?:to|over|/|:)\s+([A-Za-z0-9_\.]+)", low)
        if m:
            a, b = m.group(1), m.group(2)
            expr = f"({a})/({b})"
            return {"kind": "expr", "expr": expr, "operands": [a, b]}
        # 'gain = A/B' style
        m = re.search(r"gain\s*=\s*([A-Za-z0-9_\.]+)\s*(?:/|per|over)\s*([A-Za-z0-9_\.]+)", low)
        if m:
            a, b = m.group(1), m.group(2)
            expr = f"({a})/({b})"
            return {"kind": "expr", "expr": expr, "operands": [a, b]}

    # multiplication: 'X multiplied by Y', 'X times Y'
    m = re.search(r"([A-Za-z0-9_\.]+)\s+(?:multiplied by|times|\*)\s+([A-Za-z0-9_\.]+)", low)
    if m:
        a, b = m.group(1), m.group(2)
        expr = f"({a})*({b})"
        return {"kind": "expr", "expr": expr, "operands": [a, b]}

    # fraction words: 'half of X', 'one third of X', 'quarter of X'
    frac_map = {"half": "1/2", "one half": "1/2", "one third": "1/3", "third": "1/3", "quarter": "1/4", "one quarter": "1/4"}
    for key, val in frac_map.items():
        if key in low and " of " in low:
            # capture RHS
            m = re.search(rf"{re.escape(key)}\s+of\s+(.+)", low)
            if m:
                rhs = m.group(1).strip()
                expr = f"({val})*({rhs})"
                return {"kind": "expr", "expr": expr, "operands": [rhs]}

    # square, square root
    m = re.search(r"square root of\s+([A-Za-z0-9_\.]+)", low)
    if m:
        a = m.group(1)
        return {"kind": "expr", "expr": f"({a})**0.5", "operands": [a]}
    m = re.search(r"square of\s+([A-Za-z0-9_\.]+)", low)
    if m:
        a = m.group(1)
        return {"kind": "expr", "expr": f"({a})**2", "operands": [a]}

    # 'increase by' / 'decrease by'
    m = re.search(r"([A-Za-z0-9_\.]+)\s+increased by\s+([A-Za-z0-9_\.]+)", low)
    if m:
        a, b = m.group(1), m.group(2)
        expr = f"({a}) + ({b})"
        return {"kind": "expr", "expr": expr, "operands": [a, b]}
    m = re.search(r"([A-Za-z0-9_\.]+)\s+decreased by\s+([A-Za-z0-9_\.]+)", low)
    if m:
        a, b = m.group(1), m.group(2)
        expr = f"({a}) - ({b})"
        return {"kind": "expr", "expr": expr, "operands": [a, b]}

    return {"kind": "none"}


if __name__ == "__main__":
    tests = [
        "E = mc2",
        "E = m c^2",
        "n(n+1)/2",
        "\u03B4U = Q - W",  # ΔU
        "\$1/2\$",
    ]
    for t in tests:
        print(t, '->', normalize_fragment(t))
