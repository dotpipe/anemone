import json
import os
import re

# Load cross-glossary sections
with open('cross_glossary_sections.json', 'r', encoding='utf-8') as f:
    sections = json.load(f)

# Simple verb detector (English, not perfect)
verb_patterns = [
    r'ing$', r'ed$', r'es$', r's$', r'ify$', r'ate$', r'ize$', r'ise$', r'fy$', r'ise$', r'ise$', r'ify$', r'ise$', r'ize$'
]
common_verbs = set([
    'add', 'adding', 'change', 'changing', 'remove', 'removing', 'represent', 'represents', 'solve', 'solving', 'compute', 'computing', 'expand', 'expanding', 'factor', 'factoring', 'isolate', 'isolating', 'undo', 'undoing', 'substitute', 'substituting', 'subtract', 'subtracting', 'divide', 'dividing', 'multiply', 'multiplying', 'eliminate', 'eliminating', 'express', 'expressing', 'require', 'requiring', 'determine', 'determining', 'raise', 'raising', 'rewrite', 'rewriting', 'appear', 'appearing', 'has', 'have', 'made', 'make', 'does', 'do', 'input', 'output', 'find', 'finding', 'use', 'using', 'calculate', 'calculating', 'define', 'defining', 'represent', 'representing', 'expand', 'expanding', 'combine', 'combining', 'group', 'grouping', 'associate', 'associating', 'cross', 'crossing', 'link', 'linking', 'relate', 'relating', 'connect', 'connecting', 'share', 'sharing', 'require', 'requiring', 'remove', 'removing', 'solve', 'solving', 'undo', 'undoing', 'substitute', 'substituting', 'subtract', 'subtracting', 'divide', 'dividing', 'multiply', 'multiplying', 'eliminate', 'eliminating', 'express', 'expressing', 'require', 'requiring', 'determine', 'determining', 'raise', 'raising', 'rewrite', 'rewriting', 'appear', 'appearing', 'has', 'have', 'made', 'make', 'does', 'do', 'input', 'output', 'find', 'finding', 'use', 'using', 'calculate', 'calculating', 'define', 'defining', 'represent', 'representing', 'expand', 'expanding', 'combine', 'combining', 'group', 'grouping', 'associate', 'associating', 'cross', 'crossing', 'link', 'linking', 'relate', 'relating', 'connect', 'connecting', 'share', 'sharing'
])

def is_verb(term):
    if term in common_verbs:
        return True
    for pat in verb_patterns:
        if re.search(pat, term):
            return True
    return False

# Extract cross-reference groups with verbs
cross_groups = []
for section in sections:
    files = section.get('files', [])
    shared_terms = section.get('shared_terms', [])
    verbs = [t for t in shared_terms if is_verb(t)]
    if verbs:
        cross_groups.append({
            'files': files,
            'verbs': verbs
        })

# Output results
with open('cross_reference_groups_with_verbs.json', 'w', encoding='utf-8') as f:
    json.dump(cross_groups, f, indent=2)

print(f"Extracted {len(cross_groups)} cross-reference groups with verbs.")
print("Results saved to cross_reference_groups_with_verbs.json")
