"""
Authentication Service
Handles user registration, login, session token lifecycle, and citizen profile features.
"""
import re
import secrets
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import query_db, execute_db, get_db_connection

TOKEN_EXPIRY_DAYS = 30
EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'


def validate_email(email: str) -> bool:
    """Validates basic email structure."""
    if not email or len(email) > 254:
        return False
    return bool(re.match(EMAIL_REGEX, email.strip()))


def register_user(email: str, full_name: str, password: str) -> dict:
    """
    Registers a new user account.
    Returns dict with user details and session token, or raises ValueError.
    """
    clean_email = (email or "").strip().lower()
    clean_name = (full_name or "").strip()

    if not validate_email(clean_email):
        raise ValueError("Please provide a valid email address.")

    if not clean_name or len(clean_name) < 2:
        raise ValueError("Full name must be at least 2 characters long.")

    if not password or len(password) < 6:
        raise ValueError("Password must be at least 6 characters long.")

    # Check for existing email
    existing = query_db("SELECT id FROM users WHERE email = ?", (clean_email,), one=True)
    if existing:
        raise ValueError("An account with this email address already exists.")

    password_hash = generate_password_hash(password)

    user_id = execute_db(
        """INSERT INTO users (email, full_name, password_hash, role)
           VALUES (?, ?, ?, 'citizen')""",
        (clean_email, clean_name, password_hash)
    )

    token = create_session(user_id)

    return {
        "token": token,
        "user": {
            "id": user_id,
            "email": clean_email,
            "full_name": clean_name,
            "role": "citizen"
        }
    }


def authenticate_user(email: str, password: str) -> dict:
    """
    Authenticates user credentials.
    Returns dict with user details and session token, or raises ValueError.
    """
    clean_email = (email or "").strip().lower()

    if not clean_email or not password:
        raise ValueError("Email and password are required.")

    user = query_db(
        "SELECT id, email, full_name, password_hash, role, created_at FROM users WHERE email = ?",
        (clean_email,),
        one=True
    )

    if not user:
        raise ValueError("Invalid email or password.")

    if not check_password_hash(user["password_hash"], password):
        raise ValueError("Invalid email or password.")

    token = create_session(user["id"])

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "role": user["role"],
            "created_at": user["created_at"]
        }
    }


def create_session(user_id: int) -> str:
    """Creates and persists an active session token."""
    token = secrets.token_hex(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=TOKEN_EXPIRY_DAYS)

    execute_db(
        """INSERT INTO user_sessions (token, user_id, expires_at)
           VALUES (?, ?, ?)""",
        (token, user_id, expires_at.isoformat())
    )
    return token


def get_user_by_token(token: str) -> dict | None:
    """Retrieves user profile given an active session token."""
    if not token or not isinstance(token, str):
        return None

    clean_token = token.strip()
    session = query_db(
        """SELECT s.token, s.user_id, s.expires_at, u.id, u.email, u.full_name, u.role, u.created_at
           FROM user_sessions s
           JOIN users u ON s.user_id = u.id
           WHERE s.token = ?""",
        (clean_token,),
        one=True
    )

    if not session:
        return None

    # Check expiration if present
    if session.get("expires_at"):
        try:
            exp_str = session["expires_at"]
            # Handle both with/without timezone string format
            if "+" in exp_str or exp_str.endswith("Z"):
                exp = datetime.fromisoformat(exp_str)
                if datetime.now(timezone.utc) > exp:
                    logout_user(clean_token)
                    return None
            else:
                exp = datetime.fromisoformat(exp_str).replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > exp:
                    logout_user(clean_token)
                    return None
        except Exception:
            pass

    return {
        "id": session["id"],
        "email": session["email"],
        "full_name": session["full_name"],
        "role": session["role"],
        "created_at": session["created_at"]
    }


def logout_user(token: str) -> bool:
    """Invalidates an active session token."""
    if not token:
        return False
    execute_db("DELETE FROM user_sessions WHERE token = ?", (token.strip(),))
    return True


def save_user_checklist(user_id: int, service_code: str, service_title: str, items_checked: int, total_items: int) -> dict:
    """Saves or updates checklist progress for a user."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """INSERT INTO user_saved_checklists (user_id, service_code, service_title, items_checked, total_items, updated_at)
           VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(user_id, service_code) DO UPDATE SET
               items_checked=excluded.items_checked,
               total_items=excluded.total_items,
               updated_at=CURRENT_TIMESTAMP""",
        (user_id, service_code, service_title, items_checked, total_items)
    )
    conn.commit()
    conn.close()

    return {
        "service_code": service_code,
        "service_title": service_title,
        "items_checked": items_checked,
        "total_items": total_items
    }


def get_user_checklists(user_id: int) -> list:
    """Retrieves all saved checklists for a user."""
    return query_db(
        """SELECT service_code, service_title, items_checked, total_items, updated_at
           FROM user_saved_checklists
           WHERE user_id = ?
           ORDER BY updated_at DESC""",
        (user_id,)
    )


def seed_demo_user():
    """Seeds a standard demo citizen account if not already present."""
    demo_email = "demo@example.com"
    existing = query_db("SELECT id FROM users WHERE email = ?", (demo_email,), one=True)
    if not existing:
        password_hash = generate_password_hash("Password@123")
        execute_db(
            """INSERT INTO users (email, full_name, password_hash, role)
               VALUES (?, ?, ?, 'citizen')""",
            (demo_email, "Demo Citizen", password_hash)
        )
        print("Demo user created: demo@example.com / Password@123")
