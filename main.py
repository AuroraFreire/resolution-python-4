import sqlite3
import secrets 
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, Header

app = FastAPI()

class RegisterBody(BaseModel):
    name: str

@app.post("/register")
async def register(body: RegisterBody):
    key = create_api_key(body.name)
    return {"api_key": key, "message": "Save this key! You won't be able to see it again"}

async def verify_api_key(x_api_key: str = Header()):
    cursor.exectue("SELECT * FROM api_keys WHERE key = ?", (x_api_key))
    result = cursor.fetchone()
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return result

@app.get("/secret-data", dependencies=[Depends(verify_api_key)])
async def get_secret_data():
    return {"message": "You have access!"}

conn = sqlite3.connect("books.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS api_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT NOT NULL UNIQUE,
        owner TEXT NOT NULL
    )
""")
conn.commit()

def create_api_key(owner: str) -> str:
    key = secrets.token_hex(16)
    cursor.exectue(
        "INSERT INTO api_keys (key, owner) VALUES (?, ?)",
        (key, owner)
    )
    conn.commit()
    return key

cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        read INTEGER DEFAULT 0
    )
""")
conn.commit()

cursor.execute(
    "INSERT INTO books (title, author) VALUES (?, ?)",
    ("The Hobbit", "J.R.R Tolkien")
)
conn.commit()

cursor.execute("SELECT * FROM books WHERE author = ?", ("J.R.R Tolkien",))
results = cursor.fetchall()
for row in results:
    print(row)

cursor.execute("SELECT * FROM books")
all_books = cursor.fetchall()

cursor.execute(
    "UPDATE books SET read = 1 WHERE id = ?",
    (1,)
)
conn.commit()

cursor.execute("DELETE FROM books WHERE id = ?", (1,))
conn.commit()

@app.get("/books")
async def get_books():
    conn = sqlite3.connect("books.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    conn.close()
    return [{"id": b[0], "title": b[1], "author": b[2], "read": b[3]} for b in books]