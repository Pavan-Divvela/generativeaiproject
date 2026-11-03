"""
Database connection and query helpers.
Supports both SQLite (local development) and TiDB / MySQL (cloud deployment via DATABASE_URL or DB_HOST).
"""
import os
import re
import ssl
import sqlite3
from urllib.parse import urlparse, unquote
from config import Config

# Check if Cloud MySQL / TiDB is configured
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DB_HOST = os.getenv("DB_HOST", "").strip()


def is_cloud_db() -> bool:
    """Returns True if MySQL / TiDB configuration is detected."""
    return bool(DATABASE_URL.startswith("mysql") or DB_HOST)


def _get_cloud_config():
    """Extracts MySQL / TiDB connection configuration."""
    if DATABASE_URL:
        # e.g. mysql://user:pass@host:port/dbname
        parsed = urlparse(DATABASE_URL)
        return {
            "host": parsed.hostname,
            "port": parsed.port or 4000,
            "user": unquote(parsed.username or "root"),
            "password": unquote(parsed.password or ""),
            "database": parsed.path.lstrip("/") or "identity_helper"
        }
    return {
        "host": os.getenv("DB_HOST", "gateway01.ap-northeast-1.prod.aws.tidbcloud.com"),
        "port": int(os.getenv("DB_PORT", 4000)),
        "user": os.getenv("DB_USER", "4X1UtANC8W83WLw.root"),
        "password": os.getenv("DB_PASSWORD", "clPAFO9LaGD8YemB"),
        "database": os.getenv("DB_NAME", "identity_helper")
    }


def get_db_connection():
    """Returns a database connection (PyMySQL for TiDB/Cloud or SQLite for local)."""
    if is_cloud_db():
        import pymysql
        import pymysql.cursors

        cfg = _get_cloud_config()
        ctx = ssl.create_default_context()
        return pymysql.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            ssl=ctx,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
    else:
        Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(Config.DATABASE_PATH))
        conn.row_factory = sqlite3.Row
        return conn


def _format_query(query: str) -> str:
    """Translates parameter placeholders: '?' for SQLite, '%s' for MySQL/TiDB."""
    if is_cloud_db():
        # Replace ? with %s for MySQL parameter binding
        return query.replace("?", "%s")
    return query


def query_db(query: str, args=(), one: bool = False):
    """Executes a SELECT query and returns dictionary results."""
    conn = get_db_connection()
    formatted_query = _format_query(query)

    try:
        cur = conn.cursor()
        cur.execute(formatted_query, args)
        rows = cur.fetchall()

        if is_cloud_db():
            result = list(rows)
        else:
            result = [dict(row) for row in rows]

        return (result[0] if result else None) if one else result
    finally:
        conn.close()


def execute_db(query: str, args=()):
    """Executes an INSERT, UPDATE, or DELETE query and returns the last inserted row id."""
    conn = get_db_connection()
    formatted_query = _format_query(query)

    try:
        cur = conn.cursor()
        cur.execute(formatted_query, args)
        if not is_cloud_db():
            conn.commit()
        last_id = cur.lastrowid
        return last_id
    finally:
        conn.close()


def init_db():
    """Initializes the database schema if tables do not exist."""
    if is_cloud_db():
        # TiDB / MySQL schema tables
        tables = [
            """CREATE TABLE IF NOT EXISTS services (
                id INT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(100) UNIQUE NOT NULL,
                category VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                mode VARCHAR(50) NOT NULL,
                fee VARCHAR(100) NOT NULL,
                timeline VARCHAR(100) NOT NULL,
                official_url VARCHAR(500) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS acceptable_documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(50) NOT NULL,
                proof_type VARCHAR(50) NOT NULL,
                document_name VARCHAR(255) NOT NULL,
                issuer VARCHAR(255),
                notes TEXT,
                is_popular INT DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS discrepancy_rules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                case_type VARCHAR(100) NOT NULL,
                affected_docs VARCHAR(255) NOT NULL,
                severity VARCHAR(50) NOT NULL,
                explanation TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                affidavit_required INT DEFAULT 0,
                gazette_required INT DEFAULT 0
            )""",
            """CREATE TABLE IF NOT EXISTS faqs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(50) NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                tags TEXT
            )""",
            """CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'citizen',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS user_sessions (
                token VARCHAR(128) PRIMARY KEY,
                user_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )""",
            """CREATE TABLE IF NOT EXISTS user_saved_checklists (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                service_code VARCHAR(100) NOT NULL,
                service_title VARCHAR(255) NOT NULL,
                items_checked INT DEFAULT 0,
                total_items INT DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE KEY uk_user_service (user_id, service_code)
            )"""
        ]
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                for sql in tables:
                    cur.execute(sql)
        finally:
            conn.close()
    else:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            with open(Config.SCHEMA_PATH, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            cursor.executescript(schema_sql)
            conn.commit()
        finally:
            conn.close()
