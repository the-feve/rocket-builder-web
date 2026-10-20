"""Class sharing without student accounts (classroom use; owner approved 2026-10-19).

A teacher (a signed-in account, see accounts.py) creates a class and gets a
short class code. Students on any device type the code and a first name or
nickname to hand in the design on their screen; the teacher's class page
lists what came in. Students have no account, no email and no password.

Privacy (the site is used by children under 13; COPPA): the only thing kept
about a student is the nickname they type (the page asks for a first name or
nickname, never a full name), next to the design they hand in. No IP address,
device id or cookie is stored with it, and nothing here logs nicknames. The
per-address rate limit in app.py is an in-memory counter that never sees the
nickname. Classes and their submissions are deleted RETENTION_DAYS after the
class was made (purge(), run at startup and at most hourly after that), or
straight away when the teacher deletes them.

Stored in the designs SQLite file (ROCKETGEN_DB): tables `classes` and
`class_submissions`.
"""

from __future__ import annotations

import json
import re
import secrets
import sqlite3
import time

import designs

# Class codes: 6 characters with no look-alikes (no 0/O, 1/I/L), so a code
# read off a projector or a whiteboard is typed right. 31^6 = 887 million.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LEN = 6
RETENTION_DAYS = 180
MAX_SUBMISSIONS = 60  # per class
MAX_OPEN_CLASSES = 10  # per teacher
MAX_CLASS_NAME = 60
MAX_NICKNAME = 20
NICKNAME_RE = re.compile(r"^[^\W_][\w .'\-]*$", re.UNICODE)  # starts with a letter or digit; then letters, digits, spaces . ' -

_SCHEMA = """
CREATE TABLE IF NOT EXISTS classes (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    teacher TEXT NOT NULL,
    name TEXT NOT NULL,
    created_at REAL NOT NULL,
    closed INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS class_submissions (
    id TEXT PRIMARY KEY,
    class_id TEXT NOT NULL,
    nickname TEXT NOT NULL,
    design_name TEXT NOT NULL,
    params TEXT NOT NULL,
    summary TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS class_submissions_class ON class_submissions (class_id);
"""


class ClassError(ValueError):
    """A user-facing problem (the message is shown as is). `status` is the HTTP code."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _db() -> sqlite3.Connection:
    con = designs._db()
    con.executescript(_SCHEMA)
    return con


def normalize_code(code: str) -> str:
    """Upper case, with spaces and dashes dropped (codes are shown as ABC-123 style pairs on the class page)."""
    return re.sub(r"[\s\-]", "", (code or "")).upper()


def clean_nickname(nickname: str) -> str:
    n = re.sub(r"\s+", " ", (nickname or "").strip())
    if not n:
        raise ClassError("Type your first name or a nickname.")
    if len(n) > MAX_NICKNAME:
        raise ClassError(f"Use a short first name or nickname ({MAX_NICKNAME} letters at most).")
    if "@" in n or re.search(r"\d{3,}", n) or not NICKNAME_RE.match(n):
        raise ClassError("Use just a first name or a nickname: letters, and no email or phone number.")
    return n


def expires_at(created_at: float) -> float:
    return created_at + RETENTION_DAYS * 86400


def _class(row, count: int | None = None) -> dict:
    out = {"id": row["id"], "code": row["code"], "name": row["name"], "created_at": row["created_at"],
           "expires_at": expires_at(row["created_at"]), "closed": bool(row["closed"])}
    if count is not None:
        out["submissions"] = count
    return out


def _submission(row) -> dict:
    return {"id": row["id"], "nickname": row["nickname"], "design_name": row["design_name"],
            "params": json.loads(row["params"]), "summary": json.loads(row["summary"]),
            "created_at": row["created_at"], "updated_at": row["updated_at"]}


def _alive(now: float | None = None) -> float:
    """Classes made after this time are still kept."""
    return (now or time.time()) - RETENTION_DAYS * 86400


def create(teacher: str, name: str) -> dict:
    name = re.sub(r"\s+", " ", (name or "").strip())[:MAX_CLASS_NAME] or "My class"
    with _db() as con:
        n = con.execute("SELECT COUNT(*) FROM classes WHERE teacher = ? AND closed = 0 AND created_at > ?",
                        (teacher, _alive())).fetchone()[0]
        if n >= MAX_OPEN_CLASSES:
            raise ClassError(f"You have {n} open classes, the most at once. Close or delete one first.", 409)
        while True:
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LEN))
            class_id = secrets.token_urlsafe(9)
            try:
                con.execute("INSERT INTO classes (id, code, teacher, name, created_at, closed) VALUES (?, ?, ?, ?, ?, 0)",
                            (class_id, code, teacher, name, time.time()))
                break
            except sqlite3.IntegrityError:
                continue
    return get(class_id, teacher)


def list_for(teacher: str) -> list[dict]:
    with _db() as con:
        rows = con.execute("SELECT c.*, (SELECT COUNT(*) FROM class_submissions s WHERE s.class_id = c.id) AS n "
                           "FROM classes c WHERE c.teacher = ? AND c.created_at > ? ORDER BY c.created_at DESC",
                           (teacher, _alive())).fetchall()
    return [_class(r, r["n"]) for r in rows]


def get(class_id: str, teacher: str) -> dict | None:
    """The class with its submissions, newest first; None unless `teacher` made it."""
    with _db() as con:
        row = con.execute("SELECT * FROM classes WHERE id = ? AND teacher = ? AND created_at > ?",
                          (class_id, teacher, _alive())).fetchone()
        if not row:
            return None
        subs = con.execute("SELECT * FROM class_submissions WHERE class_id = ? ORDER BY updated_at DESC", (class_id,)).fetchall()
    return {**_class(row, len(subs)), "items": [_submission(s) for s in subs]}


def set_closed(class_id: str, teacher: str, closed: bool) -> dict | None:
    with _db() as con:
        if not closed:
            n = con.execute("SELECT COUNT(*) FROM classes WHERE teacher = ? AND closed = 0 AND created_at > ? AND id != ?",
                            (teacher, _alive(), class_id)).fetchone()[0]
            if n >= MAX_OPEN_CLASSES:
                raise ClassError(f"You have {n} open classes, the most at once. Close one first.", 409)
        con.execute("UPDATE classes SET closed = ? WHERE id = ? AND teacher = ?", (int(closed), class_id, teacher))
    return get(class_id, teacher)


def delete(class_id: str, teacher: str) -> bool:
    with _db() as con:
        cur = con.execute("DELETE FROM classes WHERE id = ? AND teacher = ?", (class_id, teacher))
        if cur.rowcount:
            con.execute("DELETE FROM class_submissions WHERE class_id = ?", (class_id,))
    return cur.rowcount == 1


def delete_submission(class_id: str, sub_id: str, teacher: str) -> bool:
    with _db() as con:
        if not con.execute("SELECT 1 FROM classes WHERE id = ? AND teacher = ?", (class_id, teacher)).fetchone():
            return False
        cur = con.execute("DELETE FROM class_submissions WHERE id = ? AND class_id = ?", (sub_id, class_id))
    return cur.rowcount == 1


def submission_for_teacher(sub_id: str, teacher: str) -> dict | None:
    """One submission (to open in the designer), only for the class's teacher."""
    with _db() as con:
        row = con.execute("SELECT s.* FROM class_submissions s JOIN classes c ON c.id = s.class_id "
                          "WHERE s.id = ? AND c.teacher = ? AND c.created_at > ?", (sub_id, teacher, _alive())).fetchone()
    return _submission(row) if row else None


def lookup(code: str) -> dict | None:
    """What a student sees after typing a code: the class name and whether it takes designs."""
    with _db() as con:
        row = con.execute("SELECT * FROM classes WHERE code = ? AND created_at > ?", (normalize_code(code), _alive())).fetchone()
    return {"code": row["code"], "name": row["name"], "open": not row["closed"]} if row else None


def submit(code: str, nickname: str, design_name: str, params: dict, summary: dict) -> dict:
    """Hands a design in to the class with this code. The same nickname
    handing in again replaces its earlier design (students keep improving
    theirs), so the class cap counts students, not attempts."""
    nickname = clean_nickname(nickname)
    design_name = re.sub(r"\s+", " ", (design_name or "").strip())[:80] or "My rocket"
    now = time.time()
    with _db() as con:
        row = con.execute("SELECT * FROM classes WHERE code = ? AND created_at > ?", (normalize_code(code), _alive())).fetchone()
        if not row:
            raise ClassError("There's no class with that code. Check it with your teacher.", 404)
        if row["closed"]:
            raise ClassError("This class isn't taking rockets any more. Ask your teacher.", 409)
        same = con.execute("SELECT id FROM class_submissions WHERE class_id = ? AND nickname = ? COLLATE NOCASE",
                           (row["id"], nickname)).fetchone()
        if same:
            sub_id = same["id"]
            con.execute("UPDATE class_submissions SET nickname = ?, design_name = ?, params = ?, summary = ?, updated_at = ? "
                        "WHERE id = ?", (nickname, design_name, json.dumps(params), json.dumps(summary), now, sub_id))
            replaced = True
        else:
            n = con.execute("SELECT COUNT(*) FROM class_submissions WHERE class_id = ?", (row["id"],)).fetchone()[0]
            if n >= MAX_SUBMISSIONS:
                raise ClassError(f"This class already has {MAX_SUBMISSIONS} rockets, the most it can hold. Ask your teacher.", 409)
            sub_id = secrets.token_urlsafe(9)
            con.execute("INSERT INTO class_submissions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (sub_id, row["id"], nickname, design_name, json.dumps(params), json.dumps(summary), now, now))
            replaced = False
    return {"id": sub_id, "class": row["name"], "nickname": nickname, "design_name": design_name, "replaced": replaced}


_last_purge = 0.0


def purge(now: float | None = None, force: bool = False) -> int:
    """Deletes classes made more than RETENTION_DAYS ago, with their
    submissions (and any submission left without a class). Runs at most
    once an hour unless forced. Returns the number of classes deleted."""
    global _last_purge
    now = now or time.time()
    if not force and now - _last_purge < 3600:
        return 0
    _last_purge = now
    cutoff = _alive(now)
    with _db() as con:
        cur = con.execute("DELETE FROM classes WHERE created_at <= ?", (cutoff,))
        con.execute("DELETE FROM class_submissions WHERE created_at <= ? OR class_id NOT IN (SELECT id FROM classes)", (cutoff,))
    return cur.rowcount
