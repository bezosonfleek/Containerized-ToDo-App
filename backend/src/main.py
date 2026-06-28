from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import List, Optional
import psycopg2
import psycopg2.extras
import psycopg2.pool
import os
import logging

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Connection pool (created once on startup) ─────────────────────────────────
pool: psycopg2.pool.SimpleConnectionPool = None

def get_conn():
    return pool.getconn()

def release_conn(conn):
    pool.putconn(conn)

# ── Lifespan (replaces deprecated @app.on_event) ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    logger.info("Starting up — connecting to database...")
    pool = psycopg2.pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        host=os.environ["DB_HOST"],        # fail fast if missing — no silent defaults
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id          SERIAL PRIMARY KEY,
                title       TEXT NOT NULL,
                description TEXT,
                completed   BOOLEAN DEFAULT FALSE,
                created_at  TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        conn.commit()
        cur.close()
        logger.info("Database ready.")
    finally:
        release_conn(conn)

    yield  # app runs here

    logger.info("Shutting down — closing connection pool.")
    pool.closeall()

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Todo API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Schema ────────────────────────────────────────────────────────────────────
class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("title must not be blank")
        return v

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class Todo(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    """Used by load balancers and monitoring to verify the service is alive."""
    return {"status": "ok"}

@app.get("/todos", response_model=List[Todo])
def list_todos():
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM todos ORDER BY created_at DESC")
        return cur.fetchall()
    finally:
        cur.close()
        release_conn(conn)

@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(todo: TodoCreate):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "INSERT INTO todos (title, description) VALUES (%s, %s) RETURNING *",
            (todo.title, todo.description),
        )
        new = cur.fetchone()
        conn.commit()
        return new
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_conn(conn)

@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM todos WHERE id = %s", (todo_id,))
        todo = cur.fetchone()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo not found")
        return todo
    finally:
        cur.close()
        release_conn(conn)

@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, updates: TodoUpdate):
    fields = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    conn = get_conn()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        set_clause = ", ".join(f"{k} = %s" for k in fields)
        values = list(fields.values()) + [todo_id]
        cur.execute(f"UPDATE todos SET {set_clause} WHERE id = %s RETURNING *", values)
        updated = cur.fetchone()
        if not updated:
            raise HTTPException(status_code=404, detail="Todo not found")
        conn.commit()
        return updated
    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_conn(conn)

@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM todos WHERE id = %s RETURNING id", (todo_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Todo not found")
        conn.commit()
    except HTTPException:
        raise
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        release_conn(conn)
