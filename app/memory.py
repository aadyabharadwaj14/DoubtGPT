import json
import sqlite3
import threading
from pathlib import Path
from typing import Any, Optional


class SQLiteSessionStore:
    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(
            self._db_path,
            check_same_thread=False,
        )
        self._connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self) -> None:
        with self._lock:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    decision TEXT,
                    confidence REAL,
                    reason TEXT,
                    debug_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            self._connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_session_id
                ON messages(session_id, id)
                """
            )
            self._connection.commit()

    def add_turn(
        self,
        session_id: str,
        role: str,
        content: str,
        decision: Optional[str] = None,
        confidence: Optional[float] = None,
        reason: Optional[str] = None,
        debug: Optional[dict[str, Any]] = None,
    ) -> None:
        debug_json = json.dumps(debug) if debug is not None else None
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO sessions (session_id)
                VALUES (?)
                ON CONFLICT(session_id) DO NOTHING
                """,
                (session_id,),
            )
            self._connection.execute(
                """
                INSERT INTO messages (
                    session_id,
                    role,
                    content,
                    decision,
                    confidence,
                    reason,
                    debug_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    role,
                    content,
                    decision,
                    confidence,
                    reason,
                    debug_json,
                ),
            )
            self._connection.execute(
                """
                UPDATE sessions
                SET updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                """,
                (session_id,),
            )
            self._connection.commit()

    def get_history(self, session_id: str) -> list[dict[str, str]]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT role, content
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

        return [{"role": row["role"], "content": row["content"]} for row in rows]

    def get_session_messages(self, session_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT
                    session_id,
                    role,
                    content,
                    decision,
                    confidence,
                    reason,
                    debug_json,
                    created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
                """,
                (session_id,),
            ).fetchall()

        messages = []
        for row in rows:
            messages.append(
                {
                    "session_id": row["session_id"],
                    "role": row["role"],
                    "content": row["content"],
                    "decision": row["decision"],
                    "confidence": row["confidence"],
                    "reason": row["reason"],
                    "debug": json.loads(row["debug_json"])
                    if row["debug_json"]
                    else None,
                    "created_at": row["created_at"],
                }
            )
        return messages

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                """
                SELECT
                    s.session_id,
                    s.title,
                    COALESCE(s.updated_at, MAX(m.created_at)) AS last_updated,
                    COUNT(m.id) AS message_count,
                    COALESCE(
                        s.title,
                        MAX(CASE WHEN m.role = 'user' THEN m.content END),
                        MAX(m.content),
                        'New chat'
                    ) AS preview
                FROM sessions s
                LEFT JOIN messages m ON s.session_id = m.session_id
                GROUP BY s.session_id, s.title, s.updated_at
                ORDER BY last_updated DESC
                """
            ).fetchall()

        sessions = []
        for row in rows:
            preview = row["preview"] or "New chat"
            if len(preview) > 64:
                preview = preview[:61] + "..."
            sessions.append(
                {
                    "session_id": row["session_id"],
                    "title": row["title"],
                    "preview": preview,
                    "last_updated": row["last_updated"],
                    "message_count": row["message_count"],
                }
            )
        return sessions

    def rename_session(self, session_id: str, title: str) -> None:
        normalized_title = title.strip()
        with self._lock:
            self._connection.execute(
                """
                INSERT INTO sessions (session_id, title)
                VALUES (?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    title = excluded.title,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (session_id, normalized_title),
            )
            self._connection.commit()

    def delete_session(self, session_id: str) -> None:
        with self._lock:
            self._connection.execute(
                "DELETE FROM messages WHERE session_id = ?",
                (session_id,),
            )
            self._connection.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            self._connection.commit()
