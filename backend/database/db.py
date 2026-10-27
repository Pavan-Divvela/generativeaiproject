import sqlite3
from pathlib import Path
from config import Config

def get_db_connection():
    """Returns a SQLite connection with row factory enabled."""
    Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(Config.DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if tables do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    with open(Config.SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    """Convenience helper to query database and return dictionary rows."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    
    result = [dict(row) for row in rows]
    return (result[0] if result else None) if one else result

def execute_db(query, args=()):
    """Executes an INSERT, UPDATE, or DELETE query."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id
