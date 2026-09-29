"""SQLite database access.

Everything goes through get_db(). Flask keeps one connection per request
(stored on `g`) and closes it automatically -- see close_db() and app.py.

We use sqlite3.Row as the row factory so query results behave like
dictionaries (row["title"]), which is easier to read in templates.
"""

import sqlite3
from pathlib import Path

from flask import g

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    field TEXT,                 -- 분야 (예: 자격증, 공모전)
    target_date TEXT,           -- YYYY-MM-DD, 없으면 NULL
    memo TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS newsletters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    sender TEXT,
    received_date TEXT,         -- YYYY-MM-DD
    category TEXT NOT NULL DEFAULT '기타',
    summary TEXT,
    body TEXT,                  -- 수동으로 붙여넣은 경우에만 채워짐 (Gmail 원문은 저장하지 않음)
    topics TEXT,                -- 쉼표로 구분된 키워드
    deadline TEXT,               -- YYYY-MM-DD 또는 '날짜 확인 필요' 또는 NULL
    status TEXT NOT NULL DEFAULT '새 소식',   -- 새 소식 / 확인함 / 보관함
    source TEXT NOT NULL DEFAULT '직접 입력', -- 직접 입력 / Gmail / 샘플
    source_link TEXT,           -- Gmail 원문 링크 (Gmail로 가져온 경우)
    goal_id INTEGER REFERENCES goals(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    date TEXT,                  -- YYYY-MM-DD, 없으면 NULL ('날짜 확인 필요' 상태로 표시)
    type TEXT NOT NULL DEFAULT '일반 일정', -- 접수 마감/시험일/행사일/준비 할 일/일반 일정
    status TEXT NOT NULL DEFAULT '예정',     -- 예정 / 완료
    goal_id INTEGER REFERENCES goals(id) ON DELETE SET NULL,
    newsletter_id INTEGER REFERENCES newsletters(id) ON DELETE SET NULL,
    source_note TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Single row (id = 1): the one connected Gmail account, if any.
CREATE TABLE IF NOT EXISTS gmail_account (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    email TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    access_token TEXT,
    token_expiry TEXT,
    connected_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_synced_at TEXT
);
"""


def get_db() -> sqlite3.Connection:
    """Return the request-scoped connection, creating it on first use."""
    if "db" not in g:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exception=None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(connection: sqlite3.Connection | None = None) -> None:
    """Create tables if they don't exist yet. Safe to call every startup."""
    db = connection or get_db()
    db.executescript(SCHEMA)
    db.commit()
