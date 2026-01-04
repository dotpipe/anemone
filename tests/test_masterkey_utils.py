from scripts import masterkey


def test_extract_subject_basic():
    meta = masterkey.extract_subject('Create a REST API for managing todo items in Python')
    assert 'rest api' in meta['subject'].lower() or 'api' in meta['subject'].lower()
    assert meta.get('language') in (None, 'python')


def test_generate_pseudocode_depth():
    pseudo = masterkey.generate_pseudocode('sample subject', depth=2)
    assert any('Clarify inputs' in s or 'Design data structures' in s for s in pseudo)


def test_parse_pseudocode_lines_and_generate():
    lines = [
        'endpoint GET /hello -> Hello World',
        'endpoint POST /items -> create_item',
        'function process_item: validate and transform the incoming item'
    ]
    parsed = masterkey.parse_pseudocode_lines(lines)
    assert len(parsed['endpoints']) == 2
    code = masterkey.generate_code_from_pseudocode('Test API', parsed)
    assert 'def' in code and 'app = FastAPI' in code
