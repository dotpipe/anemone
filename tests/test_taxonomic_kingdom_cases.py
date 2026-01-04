import pytest
from scripts.taxonomic_kingdom import (
    generate_kingdom,
    generate_combined_module,
    run_layers_collect,
)


def test_generate_kingdom_has_all_layers():
    k = generate_kingdom('python', 'sample')
    assert set(k.keys()) == {'access', 'variable', 'conditional', 'loop', 'function', 'global', 'include', 'files'}


def test_generate_combined_inside_out_orders_files_first():
    s = generate_combined_module('sample', inside_out=True)
    assert s.index('---- Layer: FILES ----') < s.index('---- Layer: ACCESS ----')


def test_run_layers_collect_without_entry_ok():
    collected = run_layers_collect(None)
    assert isinstance(collected, dict)
    # should at least include access and files layers
    assert 'access' in collected and 'files' in collected


def test_unsupported_language_raises():
    with pytest.raises(ValueError):
        generate_kingdom('javascript', 'sample')


def test_loop_files_snippet_present_when_requested():
    k = generate_kingdom('python', 'sample', loop_files=True)
    assert 'singularity' in k['files'] or 'dump.log' in k['files']


def test_long_entry_name_handles():
    long = 'x' * 2000
    k = generate_kingdom('python', long)
    assert 'Entry:' in k['access']
