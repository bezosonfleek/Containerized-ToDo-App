from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import psycopg2
import psycopg2.extras
import os

app = FastAPI(title="Todo API", version="1.0.0")

# ── DB connection ────────────────────────────────────────────────────────────
def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "todos"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )

# ── Schema ───────────────────────────────────────────────────────────────────
class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class Todo(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool

# ── Init DB on startup ───────────────────────────────────────────────────────
@app.on_event("startup")
def startup():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id          SERIAL PRIMARY KEY,
            title       TEXT NOT NULL,
            description TEXT,
            completed   BOOLEAN DEFAULT FALSE
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Todo API is running 🚀"}

@app.get("/todos", response_model=List[Todo])
def list_todos():
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM todos ORDER BY id")
    todos = cur.fetchall()
    cur.close()
    conn.close()
    return todos

@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(todo: TodoCreate):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "INSERT INTO todos (title, description) VALUES (%s, %s) RETURNING *",
        (todo.title, todo.description),
    )
    new = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return new

@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM todos WHERE id = %s", (todo_id,))
    todo = cur.fetchone()
    cur.close()
    conn.close()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, updates: TodoUpdate):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    fields = {k: v for k, v in updates.dict().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [todo_id]

    cur.execute(
        f"UPDATE todos SET {set_clause} WHERE id = %s RETURNING *", values
    )
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not updated:
        raise HTTPException(status_code=404, detail="Todo not found")
    return updated

@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM todos WHERE id = %s RETURNING id", (todo_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail="Todo not found")
