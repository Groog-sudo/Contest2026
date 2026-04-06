from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MentoringRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    lead_id TEXT PRIMARY KEY,
                    student_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    course_interest TEXT NOT NULL,
                    learning_goal TEXT NOT NULL,
                    preferred_call_time TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS calls (
                    call_id TEXT PRIMARY KEY,
                    lead_id TEXT NOT NULL,
                    student_question TEXT NOT NULL,
                    status TEXT NOT NULL,
                    script_preview TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS call_transcript_turns (
                    turn_id TEXT PRIMARY KEY,
                    transcript_id TEXT NOT NULL,
                    call_id TEXT NOT NULL,
                    lead_id TEXT NOT NULL,
                    speaker TEXT NOT NULL,
                    utterance TEXT NOT NULL,
                    turn_index INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS assessments (
                    assessment_id TEXT PRIMARY KEY,
                    lead_id TEXT NOT NULL,
                    level TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    recommended_course TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_documents (
                    document_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def save_lead(
        self,
        *,
        lead_id: str,
        student_name: str,
        phone_number: str,
        course_interest: str,
        learning_goal: str,
        preferred_call_time: str | None,
    ) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO leads (
                    lead_id,
                    student_name,
                    phone_number,
                    course_interest,
                    learning_goal,
                    preferred_call_time,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    student_name,
                    phone_number,
                    course_interest,
                    learning_goal,
                    preferred_call_time,
                    _utc_now(),
                ),
            )
            connection.commit()

    def get_lead(self, lead_id: str) -> dict[str, str] | None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT lead_id, student_name, phone_number, course_interest, learning_goal
                FROM leads
                WHERE lead_id = ?
                """,
                (lead_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return {
            "lead_id": row["lead_id"],
            "student_name": row["student_name"],
            "phone_number": row["phone_number"],
            "course_interest": row["course_interest"],
            "learning_goal": row["learning_goal"],
        }

    def save_call(
        self,
        *,
        call_id: str,
        lead_id: str,
        student_question: str,
        status: str,
        script_preview: str,
    ) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO calls (
                    call_id,
                    lead_id,
                    student_question,
                    status,
                    script_preview,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id,
                    lead_id,
                    student_question,
                    status,
                    script_preview,
                    _utc_now(),
                ),
            )
            connection.commit()

    def call_exists(self, call_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT 1 FROM calls WHERE call_id = ? LIMIT 1",
                (call_id,),
            )
            return cursor.fetchone() is not None

    def save_transcript_turns(
        self,
        *,
        call_id: str,
        lead_id: str,
        turns: list[dict[str, str]],
    ) -> tuple[str, int]:
        transcript_id = str(uuid4())
        created_at = _utc_now()

        with self._connect() as connection:
            cursor = connection.cursor()
            for index, turn in enumerate(turns, start=1):
                cursor.execute(
                    """
                    INSERT INTO call_transcript_turns (
                        turn_id,
                        transcript_id,
                        call_id,
                        lead_id,
                        speaker,
                        utterance,
                        turn_index,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid4()),
                        transcript_id,
                        call_id,
                        lead_id,
                        turn["speaker"],
                        turn["utterance"],
                        index,
                        created_at,
                    ),
                )
            connection.commit()

        return transcript_id, len(turns)

    def list_recent_utterances(self, *, lead_id: str, limit: int = 6) -> list[dict[str, str]]:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT speaker, utterance
                FROM call_transcript_turns
                WHERE lead_id = ?
                ORDER BY created_at DESC, turn_index DESC
                LIMIT ?
                """,
                (lead_id, limit),
            )
            rows = cursor.fetchall()

        return [
            {"speaker": row["speaker"], "utterance": row["utterance"]}
            for row in rows
        ]

    def save_assessment(
        self,
        *,
        assessment_id: str,
        lead_id: str,
        level: str,
        score: int,
        recommended_course: str,
        rationale: str,
    ) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO assessments (
                    assessment_id,
                    lead_id,
                    level,
                    score,
                    recommended_course,
                    rationale,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assessment_id,
                    lead_id,
                    level,
                    score,
                    recommended_course,
                    rationale,
                    _utc_now(),
                ),
            )
            connection.commit()

    def save_document(self, *, document_id: str, filename: str, status: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO knowledge_documents (
                    document_id,
                    filename,
                    status,
                    created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (document_id, filename, status, _utc_now()),
            )
            connection.commit()
