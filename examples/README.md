Hello API example

This is a tiny FastAPI app that exposes a single endpoint `/hello` returning `{"message": "Hello World"}`.

Run locally:

```powershell
pip install fastapi uvicorn
uvicorn examples.hello_api:app --reload --port 8000
```

Then visit: http://127.0.0.1:8000/hello
