"""Saved designs in SQLite: {id, name, params, versions, times}.

One table, no accounts yet. Each design gets a short random id (its share
link, /d/<id>) and an edit key, stored hashed, that the saving browser keeps.
When sign-in arrives, `owner` takes over from the edit key.

The database file is ROCKETGEN_DB, default data/designs.sqlite3 next to
this file.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(os.environ.get("ROCKETGEN_DB", Path(__file__).resolve().parent / "data" / "designs.sqlite3"))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS designs (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    params TEXT NOT NULL,
    generator_version TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    edit_key_hash TEXT NOT NULL,
    owner TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
)
"""


def _db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute(_SCHEMA)
    return con


def _hash(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def _public(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "name": row["name"], "params": json.loads(row["params"]),
            "generatorVersion": row["generator_version"], "schemaVersion": row["schema_version"],
            "created_at": row["created_at"], "updated_at": row["updated_at"]}


def get(design_id: str) -> dict | None:
    with _db() as con:
        row = con.execute("SELECT * FROM designs WHERE id = ?", (design_id,)).fetchone()
    return _public(row) if row else None


def check_key(design_id: str, key: str) -> bool:
    with _db() as con:
        row = con.execute("SELECT edit_key_hash FROM designs WHERE id = ?", (design_id,)).fetchone()
    return bool(row and key) and hmac.compare_digest(row["edit_key_hash"], _hash(key))


def create(name: str, params: dict, generator_version: str, schema_version: int) -> dict:
    key = secrets.token_urlsafe(18)
    now = time.time()
    with _db() as con:
        while True:
            design_id = secrets.token_urlsafe(6)  # 8 characters
            try:
                con.execute("INSERT INTO designs VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)",
                            (design_id, name, json.dumps(params), generator_version, schema_version, _hash(key), now, now))
                break
            except sqlite3.IntegrityError:
                continue
    return {**get(design_id), "edit_key": key}


def update(design_id: str, name: str, params: dict, generator_version: str, schema_version: int) -> dict:
    with _db() as con:
        con.execute("UPDATE designs SET name = ?, params = ?, generator_version = ?, schema_version = ?, updated_at = ? "
                    "WHERE id = ?", (name, json.dumps(params), generator_version, schema_version, time.time(), design_id))
    return get(design_id)


def rename(design_id: str, name: str) -> dict:
    with _db() as con:
        con.execute("UPDATE designs SET name = ?, updated_at = ? WHERE id = ?", (name, time.time(), design_id))
    return get(design_id)


def delete(design_id: str) -> None:
    with _db() as con:
        con.execute("DELETE FROM designs WHERE id = ?", (design_id,))
