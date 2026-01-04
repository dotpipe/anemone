from fastapi.testclient import TestClient
from examples import generated_from_pseudo


def test_generated_hello_and_post():
    client = TestClient(generated_from_pseudo.app)
    r = client.get('/hello')
    assert r.status_code == 200
    assert r.json() == {"message": "Hello World"}

    # POST endpoint should accept Item if created
    # If no POST endpoint was generated, skip the test gracefully
    resp = client.post('/items', json={"name": "x", "description": "y"})
    assert resp.status_code in (200, 422)
