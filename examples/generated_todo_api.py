from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Create A Rest Api For Managing Todo Items In Python")


class Item(BaseModel):
    id: int | None = None
    name: str
    description: str | None = None


db = {}  # simple in-memory store keyed by id


@app.get('/health')
async def health():
    return {'status': 'ok'}


@app.get('/hello')
async def hello():
    return {'message': 'Hello World'}


@app.post('/items')
async def create_item(item: Item):
    new_id = max(db.keys(), default=0) + 1
    item.id = new_id
    db[new_id] = item.dict()
    return db[new_id]


@app.get('/items/{item_id}')
async def get_item(item_id: int):
    it = db.get(item_id)
    if not it:
        raise HTTPException(status_code=404, detail='not found')
    return it


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('examples.generated_todo_api:app', host='127.0.0.1', port=8000, reload=True)
