"""Simple REST API example returning Hello World using FastAPI.

Run:
  pip install fastapi uvicorn
  uvicorn examples.hello_api:app --reload --port 8000

Endpoint:
  GET /hello -> {"message": "Hello World"}
"""
from fastapi import FastAPI

app = FastAPI(title="Hello API")


@app.get('/hello')
async def hello():
    return {"message": "Hello World"}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('examples.hello_api:app', host='127.0.0.1', port=8000, reload=True)
