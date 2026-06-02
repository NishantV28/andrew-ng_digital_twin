import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "memory.db")
LEGACY_SESSION_ID = "legacy_global"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def _table_exists(cursor: sqlite3.Cursor, table_name: str) -> bool:
    row = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _table_columns(cursor: sqlite3.Cursor, table_name: str) -> List[str]:
    rows = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [row[1] for row in rows]


def _migrate_legacy_tables(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()

    if _table_exists(cursor, "user_facts") and "session_id" not in _table_columns(cursor, "user_facts"):
        legacy_rows = cursor.execute(
            "SELECT key, value, updated_at FROM user_facts"
        ).fetchall()
        cursor.execute("DROP TABLE user_facts")
        cursor.execute(
            """
            CREATE TABLE user_facts (
                session_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (session_id, key)
            )
            """
        )
        cursor.executemany(
            "INSERT INTO user_facts (session_id, key, value, updated_at) VALUES (?, ?, ?, ?)",
            [(LEGACY_SESSION_ID, key, value, updated_at) for key, value, updated_at in legacy_rows],
        )

    if _table_exists(cursor, "topics_discussed") and "session_id" not in _table_columns(cursor, "topics_discussed"):
        legacy_rows = cursor.execute(
            "SELECT topic_name, summary, timestamp FROM topics_discussed"
        ).fetchall()
        cursor.execute("DROP TABLE topics_discussed")
        cursor.execute(
            """
            CREATE TABLE topics_discussed (
                session_id TEXT NOT NULL,
                topic_name TEXT NOT NULL,
                summary TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                PRIMARY KEY (session_id, topic_name)
            )
            """
        )
        cursor.executemany(
            "INSERT INTO topics_discussed (session_id, topic_name, summary, timestamp) VALUES (?, ?, ?, ?)",
            [(LEGACY_SESSION_ID, topic_name, summary, timestamp) for topic_name, summary, timestamp in legacy_rows],
        )

    conn.commit()


def init_db() -> None:
    conn = _connect()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_facts (
            session_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (session_id, key)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS topics_discussed (
            session_id TEXT NOT NULL,
            topic_name TEXT NOT NULL,
            summary TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            PRIMARY KEY (session_id, topic_name)
        )
        """
    )

    conn.commit()
    _migrate_legacy_tables(conn)
    conn.close()


def save_message(session_id: str, role: str, content: str) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO chat_history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (session_id, role, content, utc_now_iso()),
    )
    conn.commit()
    conn.close()


def get_chat_history(session_id: str, limit: int = 12) -> List[Dict[str, str]]:
    conn = _connect()
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT role, content
        FROM (
            SELECT id, role, content
            FROM chat_history
            WHERE session_id = ?
            ORDER BY id DESC
            LIMIT ?
        )
        ORDER BY id ASC
        """,
        (session_id, limit),
    ).fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]


def get_user_facts(session_id: str) -> Dict[str, Dict[str, str]]:
    conn = _connect()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT key, value, updated_at FROM user_facts WHERE session_id = ? ORDER BY key",
        (session_id,),
    ).fetchall()
    conn.close()
    return {row[0]: {"value": row[1], "updated_at": row[2]} for row in rows}


def update_user_fact(session_id: str, key: str, value: str) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO user_facts (session_id, key, value, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (session_id, key, value, utc_now_iso()),
    )
    conn.commit()
    conn.close()


def get_topics_discussed(session_id: str) -> Dict[str, Dict[str, str]]:
    conn = _connect()
    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT topic_name, summary, timestamp
        FROM topics_discussed
        WHERE session_id = ?
        ORDER BY timestamp DESC
        """,
        (session_id,),
    ).fetchall()
    conn.close()
    return {row[0]: {"summary": row[1], "timestamp": row[2]} for row in rows}


def add_topic_discussed(session_id: str, topic_name: str, summary: str) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO topics_discussed (session_id, topic_name, summary, timestamp)
        VALUES (?, ?, ?, ?)
        """,
        (session_id, topic_name, summary, utc_now_iso()),
    )
    conn.commit()
    conn.close()


def get_memory_state(session_id: str) -> Dict[str, Dict[str, Dict[str, str]]]:
    return {
        "user_facts": get_user_facts(session_id),
        "topics_discussed": get_topics_discussed(session_id),
    }


def reset_session_memory(session_id: str) -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM user_facts WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM topics_discussed WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def reset_all_memories() -> None:
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history")
    cursor.execute("DELETE FROM user_facts")
    cursor.execute("DELETE FROM topics_discussed")
    conn.commit()
    conn.close()


init_db()
