from fastapi.testclient import TestClient
from examples import generated_todo_api


def test_hello():
    client = TestClient(generated_todo_api.app)
    r = client.get('/hello')
    assert r.status_code == 200
    assert r.json() == {"message": "Hello World"}


def test_create_and_get_item():
    client = TestClient(generated_todo_api.app)
    payload = {"name": "Test Item", "description": "demo"}
    r = client.post('/items', json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body['id'] == 1
    assert body['name'] == payload['name']

    r2 = client.get(f"/items/{body['id']}")
    assert r2.status_code == 200
    assert r2.json()['name'] == payload['name']
