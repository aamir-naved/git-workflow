from fastapi import FastAPI, Request
from pydantic import BaseModel

# Create FastAPI app
app = FastAPI()

# Simple GET
@app.get("/")
def root():
    return {"message": "Hello from FastAPI on macOS M1!"}

# GET with path param
@app.get("/hello/{name}")
def say_hello(name: str):
    return {"message": f"Hello, {name}!"}

# POST with body validation
class Item(BaseModel):
    name: str
    price: float

@app.post("/items/")
def create_item(item: Item):
    return {"received": item.dict()}

@app.post("/webhook")
async def webhook_receiver(request: Request):
    payload = await request.json()
    print("Webhook Received: ", payload)
    return {"status":"Ok"}

