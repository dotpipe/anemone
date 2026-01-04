from scripts.taxonomic_kingdom import load_kingdom_from_json, run_loaded_kingdom


def test_load_and_run_generated_kingdom():
    path = 'data/generated_kingdoms.json'
    snippets = load_kingdom_from_json(path)
    # basic sanity: snippets map contains expected layers
    assert isinstance(snippets, dict)
    assert 'files' in snippets and 'access' in snippets

    collected = run_loaded_kingdom(path, inside_out=False)
    assert isinstance(collected, dict)
    # ensure key layers executed
    assert 'files' in collected and 'include' in collected

    include_locals = collected.get('include', {})
    files_locals = collected.get('files', {})
    # STACK should be injected into both layer namespaces and be the same object
    assert 'STACK' in include_locals and 'STACK' in files_locals
    assert include_locals['STACK'] is files_locals['STACK']
