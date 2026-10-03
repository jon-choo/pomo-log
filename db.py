"""SQLite data layer: schema + CRUD for categories, subjects, sessions, settings.

No business rules here beyond basic integrity (names required, times ordered,
foreign keys valid) - things like "what counts as this week" belong in
stats.py, not here. Categories/subjects are soft-deleted (archived) so
session history never dangles; sessions themselves can be hard-deleted since
the log is explicitly user-editable.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "pomolog.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE,
    archived INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS subjects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id),
    archived    INTEGER NOT NULL DEFAULT 0,
    UNIQUE(name, category_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id       INTEGER NOT NULL REFERENCES subjects(id),
    category_id      INTEGER NOT NULL REFERENCES categories(id),
    start_time       TEXT NOT NULL,
    end_time         TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL,
    mode             TEXT NOT NULL CHECK(mode IN ('pomodoro', 'freeform', 'manual'))
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

def create_category(name: str, db_path: Path = DEFAULT_DB_PATH) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Category name cannot be empty")
    conn = get_connection(db_path)
    try:
        try:
            cur = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        except sqlite3.IntegrityError:
            raise ValueError(f"Category '{name}' already exists")
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def rename_category(category_id: int, new_name: str, db_path: Path = DEFAULT_DB_PATH) -> None:
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("Category name cannot be empty")
    conn = get_connection(db_path)
    try:
        try:
            cur = conn.execute("UPDATE categories SET name = ? WHERE id = ?", (new_name, category_id))
        except sqlite3.IntegrityError:
            raise ValueError(f"Category '{new_name}' already exists")
        if cur.rowcount == 0:
            raise ValueError(f"No category with id {category_id}")
        conn.commit()
    finally:
        conn.close()


def archive_category(category_id: int, db_path: Path = DEFAULT_DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        cur = conn.execute("UPDATE categories SET archived = 1 WHERE id = ?", (category_id,))
        if cur.rowcount == 0:
            raise ValueError(f"No category with id {category_id}")
        conn.commit()
    finally:
        conn.close()


def list_categories(include_archived: bool = False, db_path: Path = DEFAULT_DB_PATH) -> list[dict]:
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM categories"
        if not include_archived:
            query += " WHERE archived = 0"
        query += " ORDER BY name"
        return [dict(row) for row in conn.execute(query)]
    finally:
        conn.close()


def get_category(category_id: int, db_path: Path = DEFAULT_DB_PATH) -> dict | None:
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Subjects
# ---------------------------------------------------------------------------

def create_subject(name: str, category_id: int, db_path: Path = DEFAULT_DB_PATH) -> int:
    name = name.strip()
    if not name:
        raise ValueError("Subject name cannot be empty")
    conn = get_connection(db_path)
    try:
        category = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
        if category is None:
            raise ValueError(f"No category with id {category_id}")
        if category["archived"]:
            raise ValueError(f"Category '{category['name']}' is archived; unarchive it first")
        try:
            cur = conn.execute(
                "INSERT INTO subjects (name, category_id) VALUES (?, ?)", (name, category_id)
            )
        except sqlite3.IntegrityError:
            raise ValueError(f"Subject '{name}' already exists in this category")
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def rename_subject(subject_id: int, new_name: str, db_path: Path = DEFAULT_DB_PATH) -> None:
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("Subject name cannot be empty")
    conn = get_connection(db_path)
    try:
        try:
            cur = conn.execute("UPDATE subjects SET name = ? WHERE id = ?", (new_name, subject_id))
        except sqlite3.IntegrityError:
            raise ValueError(f"Subject '{new_name}' already exists in this category")
        if cur.rowcount == 0:
            raise ValueError(f"No subject with id {subject_id}")
        conn.commit()
    finally:
        conn.close()


def recategorize_subject(subject_id: int, new_category_id: int, db_path: Path = DEFAULT_DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        category = conn.execute("SELECT * FROM categories WHERE id = ?", (new_category_id,)).fetchone()
        if category is None:
            raise ValueError(f"No category with id {new_category_id}")
        if category["archived"]:
            raise ValueError(f"Category '{category['name']}' is archived; unarchive it first")
        try:
            cur = conn.execute(
                "UPDATE subjects SET category_id = ? WHERE id = ?", (new_category_id, subject_id)
            )
        except sqlite3.IntegrityError:
            raise ValueError("Subject already exists in that category")
        if cur.rowcount == 0:
            raise ValueError(f"No subject with id {subject_id}")
        conn.commit()
    finally:
        conn.close()


def archive_subject(subject_id: int, db_path: Path = DEFAULT_DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        cur = conn.execute("UPDATE subjects SET archived = 1 WHERE id = ?", (subject_id,))
        if cur.rowcount == 0:
            raise ValueError(f"No subject with id {subject_id}")
        conn.commit()
    finally:
        conn.close()


def list_subjects(
    include_archived: bool = False,
    category_id: int | None = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> list[dict]:
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM subjects WHERE 1=1"
        params: list = []
        if not include_archived:
            query += " AND archived = 0"
        if category_id is not None:
            query += " AND category_id = ?"
            params.append(category_id)
        query += " ORDER BY name"
        return [dict(row) for row in conn.execute(query, params)]
    finally:
        conn.close()


def get_subject(subject_id: int, db_path: Path = DEFAULT_DB_PATH) -> dict | None:
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def log_session(
    subject_id: int,
    start_time: datetime,
    end_time: datetime,
    mode: str,
    db_path: Path = DEFAULT_DB_PATH,
) -> int:
    """Insert a completed session. category_id is snapshotted from the
    subject's current category so re-categorizing later doesn't rewrite
    history. Timestamps must be aware (see timeutil.utc_now)."""
    if mode not in ("pomodoro", "freeform", "manual"):
        raise ValueError(f"Invalid mode '{mode}'")
    if start_time.tzinfo is None or end_time.tzinfo is None:
        raise ValueError("start_time and end_time must be aware datetimes")
    if end_time <= start_time:
        raise ValueError("end_time must be after start_time")

    conn = get_connection(db_path)
    try:
        subject = conn.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
        if subject is None:
            raise ValueError(f"No subject with id {subject_id}")
        duration_seconds = round((end_time - start_time).total_seconds())
        cur = conn.execute(
            """INSERT INTO sessions
               (subject_id, category_id, start_time, end_time, duration_seconds, mode)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                subject_id,
                subject["category_id"],
                start_time.isoformat(),
                end_time.isoformat(),
                duration_seconds,
                mode,
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_session(
    session_id: int,
    subject_id: int | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> None:
    """Edit a logged session (for fixing mistakes). Any field left as None
    is unchanged. Recomputes duration_seconds and re-snapshots category_id
    if subject_id changes."""
    conn = get_connection(db_path)
    try:
        existing = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if existing is None:
            raise ValueError(f"No session with id {session_id}")

        new_subject_id = subject_id if subject_id is not None else existing["subject_id"]
        new_start = start_time if start_time is not None else datetime.fromisoformat(existing["start_time"])
        new_end = end_time if end_time is not None else datetime.fromisoformat(existing["end_time"])

        if new_start.tzinfo is None or new_end.tzinfo is None:
            raise ValueError("start_time and end_time must be aware datetimes")
        if new_end <= new_start:
            raise ValueError("end_time must be after start_time")

        subject = conn.execute("SELECT * FROM subjects WHERE id = ?", (new_subject_id,)).fetchone()
        if subject is None:
            raise ValueError(f"No subject with id {new_subject_id}")

        duration_seconds = round((new_end - new_start).total_seconds())
        conn.execute(
            """UPDATE sessions
               SET subject_id = ?, category_id = ?, start_time = ?, end_time = ?, duration_seconds = ?
               WHERE id = ?""",
            (
                new_subject_id,
                subject["category_id"],
                new_start.isoformat(),
                new_end.isoformat(),
                duration_seconds,
                session_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def delete_session(session_id: int, db_path: Path = DEFAULT_DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        if cur.rowcount == 0:
            raise ValueError(f"No session with id {session_id}")
        conn.commit()
    finally:
        conn.close()


def list_sessions(
    start: datetime | None = None,
    end: datetime | None = None,
    subject_id: int | None = None,
    category_id: int | None = None,
    newest_first: bool = True,
    db_path: Path = DEFAULT_DB_PATH,
) -> list[dict]:
    """Sessions whose start_time falls in [start, end), optionally filtered
    by subject or category. Omit start/end for all-time."""
    conn = get_connection(db_path)
    try:
        query = "SELECT * FROM sessions WHERE 1=1"
        params: list = []
        if start is not None:
            query += " AND start_time >= ?"
            params.append(start.isoformat())
        if end is not None:
            query += " AND start_time < ?"
            params.append(end.isoformat())
        if subject_id is not None:
            query += " AND subject_id = ?"
            params.append(subject_id)
        if category_id is not None:
            query += " AND category_id = ?"
            params.append(category_id)
        query += f" ORDER BY start_time {'DESC' if newest_first else 'ASC'}"
        return [dict(row) for row in conn.execute(query, params)]
    finally:
        conn.close()


def get_session(session_id: int, db_path: Path = DEFAULT_DB_PATH) -> dict | None:
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return _row_to_dict(row)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def get_setting(key: str, default: str | None = None, db_path: Path = DEFAULT_DB_PATH) -> str | None:
    conn = get_connection(db_path)
    try:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row is not None else default
    finally:
        conn.close()


def set_setting(key: str, value: str, db_path: Path = DEFAULT_DB_PATH) -> None:
    conn = get_connection(db_path)
    try:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        conn.commit()
    finally:
        conn.close()
