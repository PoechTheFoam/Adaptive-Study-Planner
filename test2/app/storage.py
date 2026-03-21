from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def generate_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Storage:
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    education_level TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS topic_progress (
                    id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    education_level TEXT NOT NULL,
                    current_difficulty TEXT NOT NULL,
                    mastery REAL NOT NULL DEFAULT 0,
                    avg_response_time REAL NOT NULL DEFAULT 0,
                    sessions_completed INTEGER NOT NULL DEFAULT 0,
                    last_decision TEXT NOT NULL DEFAULT '',
                    struggling INTEGER NOT NULL DEFAULT 0,
                    inconsistency_score REAL NOT NULL DEFAULT 0,
                    predicted_band TEXT NOT NULL DEFAULT 'Building',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(profile_id, topic),
                    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    education_level TEXT NOT NULL,
                    requested_difficulty TEXT NOT NULL,
                    delivered_difficulty TEXT NOT NULL,
                    content_source TEXT NOT NULL,
                    question_count INTEGER NOT NULL,
                    questions_json TEXT NOT NULL,
                    submissions_json TEXT,
                    result_json TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_sessions_profile_created
                ON sessions(profile_id, created_at DESC);

                CREATE INDEX IF NOT EXISTS idx_topic_progress_profile
                ON topic_progress(profile_id);
                """
            )

    def create_profile(self, *, name: str, education_level: str, topic: str) -> dict[str, Any]:
        now = utc_now_iso()
        profile_id = generate_id("learner")
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO profiles (id, name, education_level, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (profile_id, name, education_level, now, now),
            )
            self._ensure_topic_progress(
                conn,
                profile_id=profile_id,
                topic=topic,
                education_level=education_level,
            )
        snapshot = self.get_profile_snapshot(profile_id)
        if snapshot is None:
            raise KeyError("Profile not found after creation")
        return snapshot

    def get_profile_snapshot(self, profile_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            profile_row = conn.execute(
                "SELECT * FROM profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()
            if not profile_row:
                return None

            topic_rows = conn.execute(
                """
                SELECT * FROM topic_progress
                WHERE profile_id = ?
                ORDER BY updated_at DESC
                """,
                (profile_id,),
            ).fetchall()
            session_rows = conn.execute(
                """
                SELECT id, topic, education_level, requested_difficulty, delivered_difficulty,
                       content_source, created_at, completed_at, result_json
                FROM sessions
                WHERE profile_id = ? AND result_json IS NOT NULL
                ORDER BY created_at DESC
                LIMIT 6
                """,
                (profile_id,),
            ).fetchall()

        return {
            "profile": self._serialize_profile(profile_row),
            "topics": [self._serialize_topic(row) for row in topic_rows],
            "recentSessions": [self._serialize_session(row) for row in session_rows],
        }

    def ensure_profile_topic(self, *, profile_id: str, topic: str, education_level: str) -> dict[str, Any]:
        with self.connection() as conn:
            profile_row = conn.execute(
                "SELECT * FROM profiles WHERE id = ?",
                (profile_id,),
            ).fetchone()
            if not profile_row:
                raise KeyError("Profile not found")

            conn.execute(
                """
                UPDATE profiles
                SET education_level = ?, updated_at = ?
                WHERE id = ?
                """,
                (education_level, utc_now_iso(), profile_id),
            )
            self._ensure_topic_progress(
                conn,
                profile_id=profile_id,
                topic=topic,
                education_level=education_level,
            )

        snapshot = self.get_profile_snapshot(profile_id)
        if snapshot is None:
            raise KeyError("Profile not found after update")
        return snapshot

    def get_topic_progress(self, *, profile_id: str, topic: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM topic_progress
                WHERE profile_id = ? AND topic = ?
                """,
                (profile_id, topic),
            ).fetchone()
        return self._serialize_topic(row) if row else None

    def create_session(
        self,
        *,
        profile_id: str,
        topic: str,
        education_level: str,
        requested_difficulty: str,
        delivered_difficulty: str,
        content_source: str,
        questions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        session_id = generate_id("session")
        created_at = utc_now_iso()
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions (
                    id, profile_id, topic, education_level, requested_difficulty, delivered_difficulty,
                    content_source, question_count, questions_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    profile_id,
                    topic,
                    education_level,
                    requested_difficulty,
                    delivered_difficulty,
                    content_source,
                    len(questions),
                    json.dumps(questions),
                    created_at,
                ),
            )
        session = self.get_session(session_id)
        if session is None:
            raise KeyError("Session not found after creation")
        return session

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
        if not row:
            return None
        return {
            **dict(row),
            "questions": json.loads(row["questions_json"]),
            "submissions": json.loads(row["submissions_json"]) if row["submissions_json"] else None,
            "result": json.loads(row["result_json"]) if row["result_json"] else None,
        }

    def complete_session(
        self,
        *,
        session_id: str,
        submissions: list[dict[str, Any]],
        result: dict[str, Any],
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE sessions
                SET submissions_json = ?, result_json = ?, completed_at = ?
                WHERE id = ?
                """,
                (
                    json.dumps(submissions),
                    json.dumps(result),
                    utc_now_iso(),
                    session_id,
                ),
            )

    def save_topic_progress(
        self,
        *,
        profile_id: str,
        topic: str,
        values: dict[str, Any],
    ) -> None:
        now = utc_now_iso()
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE topic_progress
                SET education_level = ?,
                    current_difficulty = ?,
                    mastery = ?,
                    avg_response_time = ?,
                    sessions_completed = ?,
                    last_decision = ?,
                    struggling = ?,
                    inconsistency_score = ?,
                    predicted_band = ?,
                    updated_at = ?
                WHERE profile_id = ? AND topic = ?
                """,
                (
                    values["education_level"],
                    values["current_difficulty"],
                    values["mastery"],
                    values["avg_response_time"],
                    values["sessions_completed"],
                    values["last_decision"],
                    values["struggling"],
                    values["inconsistency_score"],
                    values["predicted_band"],
                    now,
                    profile_id,
                    topic,
                ),
            )
            conn.execute(
                """
                UPDATE profiles
                SET education_level = ?, updated_at = ?
                WHERE id = ?
                """,
                (values["education_level"], now, profile_id),
            )

    def _ensure_topic_progress(
        self,
        conn: sqlite3.Connection,
        *,
        profile_id: str,
        topic: str,
        education_level: str,
    ) -> None:
        now = utc_now_iso()
        existing = conn.execute(
            """
            SELECT id FROM topic_progress
            WHERE profile_id = ? AND topic = ?
            """,
            (profile_id, topic),
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE topic_progress
                SET education_level = ?, updated_at = ?
                WHERE id = ?
                """,
                (education_level, now, existing["id"]),
            )
            return

        conn.execute(
            """
            INSERT INTO topic_progress (
                id, profile_id, topic, education_level, current_difficulty, mastery,
                avg_response_time, sessions_completed, last_decision, struggling,
                inconsistency_score, predicted_band, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'medium', 0, 0, 0, 'new', 0, 0, 'Building', ?, ?)
            """,
            (
                generate_id("topic"),
                profile_id,
                topic,
                education_level,
                now,
                now,
            ),
        )

    def _serialize_profile(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "educationLevel": row["education_level"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    def _serialize_topic(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "profileId": row["profile_id"],
            "topic": row["topic"],
            "educationLevel": row["education_level"],
            "currentDifficulty": row["current_difficulty"],
            "mastery": round(float(row["mastery"]), 1),
            "avgResponseTime": round(float(row["avg_response_time"]), 1),
            "sessionsCompleted": int(row["sessions_completed"]),
            "lastDecision": row["last_decision"],
            "struggling": bool(row["struggling"]),
            "inconsistencyScore": round(float(row["inconsistency_score"]), 3),
            "predictedBand": row["predicted_band"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
        }

    def _serialize_session(self, row: sqlite3.Row) -> dict[str, Any]:
        result = json.loads(row["result_json"]) if row["result_json"] else {}
        return {
            "id": row["id"],
            "topic": row["topic"],
            "educationLevel": row["education_level"],
            "requestedDifficulty": row["requested_difficulty"],
            "deliveredDifficulty": row["delivered_difficulty"],
            "contentSource": row["content_source"],
            "createdAt": row["created_at"],
            "completedAt": row["completed_at"],
            "masteryPercent": result.get("masteryPercent"),
            "mode": result.get("decision", {}).get("mode"),
            "predictionBand": result.get("prediction", {}).get("band"),
        }
