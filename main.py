import sqlite3
import secrets
import datetime
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, Header, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded


def get_api_key(request: Request) -> str:
    return request.headers.get("x-api-key", "unknown")


limiter = Limiter(key_func=get_api_key)
app = FastAPI()
app.state.limiter = limiter


conn = sqlite3.connect("inventory.db", check_same_thread=False)
cursor = conn.cursor()


cursor.execute("""
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL UNIQUE,
        owner TEXT NOT NULL
    )
""")


cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER DEFAULT 0,
        category TEXT NOT NULL
    )
""")
conn.commit()


class RegisterBody(BaseModel):
    name: str


class ItemBody(BaseModel):
    name: str
    quantity: int
    category: str


def create_api_key(owner: str) -> str:
    key = secrets.token_hex(16)
    cursor.execute(
        "INSERT INTO api_keys (key, owner) VALUES (?, ?)",
        (key, owner)
    )
    conn.commit()
    return key


def log_event(event: str):
    with open("audit.log", "a") as f:
        f.write(f"{datetime.datetime.now()} - {event}\n")


async def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    cursor.execute("SELECT * FROM api_keys WHERE key = ?", (x_api_key,))
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return result


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later!"}
    )


@app.post("/register")
async def register(body: RegisterBody, background_tasks: BackgroundTasks):
    key = create_api_key(body.name)
    background_tasks.add_task(log_event, f"New user registered: {body.name}")
    return {"api_key": key, "message": "Save this key! You won't be able to see it again"}


@app.get("/inventory", dependencies=[Depends(verify_api_key)])
@limiter.limit("20/minute")
async def get_inventory(request: Request):
    cursor.execute("SELECT * FROM items")
    items = cursor.fetchall()
    return [{"id": i[0], "name": i[1], "quantity": i[2], "category": i[3]} for i in items]


@app.post("/inventory", dependencies=[Depends(verify_api_key)])
@limiter.limit("5/minute")
async def add_item(request: Request, body: ItemBody, background_tasks: BackgroundTasks):
    cursor.execute(
        "INSERT INTO items (name, quantity, category) VALUES (?, ?, ?)",
        (body.name, body.quantity, body.category)
    )
    conn.commit()
    background_tasks.add_task(log_event, f"Item added: {body.name}")
    return {"message": "Item added to inventory"}


@app.get("/my-info")
async def my_info(key_info = Depends(verify_api_key)):
    return {"owner": key_info[2], "key_id": key_info[0]}