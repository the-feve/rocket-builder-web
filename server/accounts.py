"""User accounts: email + password, and sign-in sessions.

Stored in the same SQLite file as the designs (ROCKETGEN_DB). Passwords are
hashed with scrypt (Python standard library; no extra dependency). A session
is a random token kept in an HttpOnly cookie; only its SHA-256 is stored, so
a copy of the database can't be used to sign in.

Designs saved while signed in get `owner` = the user's id (see designs.py).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time

import designs

SESSION_DAYS = 30
MIN_PASSWORD = 8
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at REAL NOT NULL,
    expires_at REAL NOT NULL
);
"""

# scrypt cost: about 50 ms and 16 MB per hash on a small machine.
_N, _R, _P = 2 ** 14, 8, 1


class AccountError(ValueError):
    """A user-facing problem with sign-up or sign-in."""


PREF_KEYS = {"skip_tutorial": bool}  # account settings the page can change


def _db() -> sqlite3.Connection:
    con = designs._db()
    con.executescript(_SCHEMA)
    if "prefs" not in {r[1] for r in con.execute("PRAGMA table_info(users)")}:  # added 2026-10-14
        con.execute("ALTER TABLE users ADD COLUMN prefs TEXT NOT NULL DEFAULT '{}'")
    return con


def _user(row) -> dict:
    return {"id": row["id"], "email": row["email"], "prefs": json.loads(row["prefs"] or "{}")}


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    h = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=32)
    return f"scrypt${_N}${_R}${_P}${salt.hex()}${h.hex()}"


def check_password(password: str, stored: str) -> bool:
    try:
        _, n, r, p, salt, h = stored.split("$")
        got = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=int(n), r=int(r), p=int(p), dklen=len(h) // 2)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(got.hex(), h)


def normalize_email(email: str) -> str:
    email = (email or "").strip().lower()
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise AccountError("Enter a valid email address.")
    return email


def create_user(email: str, password: str) -> dict:
    email = normalize_email(email)
    if len(password or "") < MIN_PASSWORD:
        raise AccountError(f"Use a password of at least {MIN_PASSWORD} characters.")
    user_id = secrets.token_urlsafe(9)
    try:
        with _db() as con:
            con.execute("INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                        (user_id, email, hash_password(password), time.time()))
    except sqlite3.IntegrityError:
        raise AccountError("There's already an account with that email. Sign in instead.") from None
    return {"id": user_id, "email": email, "prefs": {}}


def authenticate(email: str, password: str) -> dict | None:
    try:
        email = normalize_email(email)
    except AccountError:
        return None
    with _db() as con:
        row = con.execute("SELECT id, email, password_hash, prefs FROM users WHERE email = ?", (email,)).fetchone()
    if not row:
        hash_password(password or "")  # same time either way, so emails can't be probed by timing
        return None
    return _user(row) if check_password(password or "", row["password_hash"]) else None


def new_session(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    now = time.time()
    with _db() as con:
        con.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
        con.execute("INSERT INTO sessions VALUES (?, ?, ?, ?)", (_sha(token), user_id, now, now + SESSION_DAYS * 86400))
    return token


def user_for_session(token: str | None) -> dict | None:
    if not token:
        return None
    with _db() as con:
        row = con.execute("SELECT u.id, u.email, u.prefs FROM sessions s JOIN users u ON u.id = s.user_id "
                          "WHERE s.token_hash = ? AND s.expires_at > ?", (_sha(token), time.time())).fetchone()
    return _user(row) if row else None


def end_session(token: str | None) -> None:
    if token:
        with _db() as con:
            con.execute("DELETE FROM sessions WHERE token_hash = ?", (_sha(token),))


def get_user(user_id: str) -> dict | None:
    with _db() as con:
        row = con.execute("SELECT id, email, prefs FROM users WHERE id = ?", (user_id,)).fetchone()
    return _user(row) if row else None


def set_prefs(user_id: str, changes: dict) -> dict:
    """Merges known settings (PREF_KEYS) into the account's; returns them all."""
    user = get_user(user_id)
    prefs = {**user["prefs"], **{k: PREF_KEYS[k](v) for k, v in changes.items() if k in PREF_KEYS}}
    with _db() as con:
        con.execute("UPDATE users SET prefs = ? WHERE id = ?", (json.dumps(prefs), user_id))
    return prefs
