from __future__ import annotations

import json
import sqlite3
from datetime import datetime, time, timedelta, timezone
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
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS recordings (
                    recording_id TEXT PRIMARY KEY,
                    call_id TEXT NOT NULL,
                    lead_id TEXT NOT NULL,
                    object_key TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS async_tasks (
                    task_id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT,
                    error_message TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            self._ensure_column(
                connection=connection,
                table_name="knowledge_documents",
                column_name="chunk_count",
                column_definition="INTEGER NOT NULL DEFAULT 0",
            )
            connection.commit()

    def _ensure_column(
        self,
        *,
        connection: sqlite3.Connection,
        table_name: str,
        column_name: str,
        column_definition: str,
    ) -> None:
        cursor = connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        existing_columns = {row[1] for row in cursor.fetchall()}
        if column_name in existing_columns:
            return
        cursor.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )

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
            cursor.execute("SELECT 1 FROM calls WHERE call_id = ? LIMIT 1", (call_id,))
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

        return [{"speaker": row["speaker"], "utterance": row["utterance"]} for row in rows]

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

    def save_document(
        self,
        *,
        document_id: str,
        filename: str,
        status: str,
        chunk_count: int = 0,
    ) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO knowledge_documents (
                    document_id,
                    filename,
                    status,
                    chunk_count,
                    created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (document_id, filename, status, chunk_count, _utc_now()),
            )
            connection.commit()

    def save_recording(
        self,
        *,
        call_id: str,
        lead_id: str,
        object_key: str,
        content_type: str,
        size_bytes: int,
    ) -> str:
        recording_id = str(uuid4())
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO recordings (
                    recording_id,
                    call_id,
                    lead_id,
                    object_key,
                    content_type,
                    size_bytes,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    recording_id,
                    call_id,
                    lead_id,
                    object_key,
                    content_type,
                    size_bytes,
                    _utc_now(),
                ),
            )
            connection.commit()
        return recording_id

    def create_async_task(self, *, task_type: str, payload: dict[str, object]) -> str:
        task_id = str(uuid4())
        now = _utc_now()
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO async_tasks (
                    task_id,
                    task_type,
                    payload_json,
                    status,
                    result_json,
                    error_message,
                    attempts,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    task_type,
                    json.dumps(payload, ensure_ascii=False),
                    "queued",
                    None,
                    None,
                    0,
                    now,
                    now,
                ),
            )
            connection.commit()
        return task_id

    def get_async_task(self, task_id: str) -> dict[str, object] | None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT task_id, task_type, payload_json, status, result_json, error_message, attempts, created_at, updated_at
                FROM async_tasks
                WHERE task_id = ?
                """,
                (task_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return self._task_row_to_dict(row)

    def list_async_tasks(self, *, limit: int = 30) -> list[dict[str, object]]:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT task_id, task_type, payload_json, status, result_json, error_message, attempts, created_at, updated_at
                FROM async_tasks
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
        return [self._task_row_to_dict(row) for row in rows]

    def list_queued_tasks_for_worker(self, *, limit: int = 10) -> list[dict[str, object]]:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT task_id, task_type, payload_json, status, result_json, error_message, attempts, created_at, updated_at
                FROM async_tasks
                WHERE status = ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                ("queued", limit),
            )
            rows = cursor.fetchall()
        return [self._task_row_to_dict(row) for row in rows]

    def mark_task_processing(self, *, task_id: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE async_tasks
                SET status = ?, attempts = attempts + 1, result_json = NULL, error_message = NULL, updated_at = ?
                WHERE task_id = ?
                """,
                ("processing", _utc_now(), task_id),
            )
            connection.commit()

    def mark_task_done(self, *, task_id: str, result: dict[str, object]) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE async_tasks
                SET status = ?, result_json = ?, error_message = NULL, updated_at = ?
                WHERE task_id = ?
                """,
                ("done", json.dumps(result, ensure_ascii=False), _utc_now(), task_id),
            )
            connection.commit()

    def mark_task_failed(self, *, task_id: str, error_message: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE async_tasks
                SET status = ?, error_message = ?, updated_at = ?
                WHERE task_id = ?
                """,
                ("failed", error_message, _utc_now(), task_id),
            )
            connection.commit()

    def mark_task_requeued(self, *, task_id: str, error_message: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE async_tasks
                SET status = ?, error_message = ?, updated_at = ?
                WHERE task_id = ?
                """,
                ("queued", error_message, _utc_now(), task_id),
            )
            connection.commit()

    def get_dashboard_metrics(
        self,
        *,
        period_days: int = 7,
    ) -> dict[str, float | int | list[dict[str, int | str]]]:
        today_utc = datetime.now(timezone.utc).date()
        period_start = today_utc - timedelta(days=period_days - 1)
        since_iso = datetime.combine(period_start, time.min, tzinfo=timezone.utc).isoformat()

        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute("SELECT COUNT(*) AS count FROM leads")
            total_leads = int(cursor.fetchone()["count"])

            cursor.execute("SELECT COUNT(DISTINCT lead_id) AS count FROM calls")
            leads_with_calls = int(cursor.fetchone()["count"])

            cursor.execute("SELECT COUNT(DISTINCT lead_id) AS count FROM assessments")
            leads_with_assessments = int(cursor.fetchone()["count"])

            cursor.execute("SELECT AVG(score) AS avg_score FROM assessments")
            avg_score_value = cursor.fetchone()["avg_score"]
            avg_assessment_score = float(avg_score_value) if avg_score_value is not None else 0.0

            cursor.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM async_tasks
                GROUP BY status
                """
            )
            task_rows = cursor.fetchall()
            task_counts = {row["status"]: int(row["count"]) for row in task_rows}

            daily_leads = self._count_by_day(
                cursor=cursor,
                table_name="leads",
                since_iso=since_iso,
            )
            daily_calls = self._count_by_day(
                cursor=cursor,
                table_name="calls",
                since_iso=since_iso,
            )
            daily_assessments = self._count_by_day(
                cursor=cursor,
                table_name="assessments",
                since_iso=since_iso,
            )

        conversion_rate = (leads_with_calls / total_leads) if total_leads > 0 else 0.0
        completion_rate = (
            (leads_with_assessments / leads_with_calls) if leads_with_calls > 0 else 0.0
        )
        series: list[dict[str, int | str]] = []
        for offset in range(period_days):
            current_date = period_start + timedelta(days=offset)
            date_key = current_date.isoformat()
            series.append(
                {
                    "date": date_key,
                    "leads": daily_leads.get(date_key, 0),
                    "calls": daily_calls.get(date_key, 0),
                    "assessments": daily_assessments.get(date_key, 0),
                }
            )

        return {
            "total_leads": total_leads,
            "leads_with_calls": leads_with_calls,
            "leads_with_assessments": leads_with_assessments,
            "conversion_rate": conversion_rate,
            "completion_rate": completion_rate,
            "avg_assessment_score": avg_assessment_score,
            "queued_tasks": task_counts.get("queued", 0),
            "processing_tasks": task_counts.get("processing", 0),
            "failed_tasks": task_counts.get("failed", 0),
            "period_days": period_days,
            "series": series,
        }

    def _task_row_to_dict(self, row: sqlite3.Row) -> dict[str, object]:
        payload_json = row["payload_json"]
        result_json = row["result_json"]
        return {
            "task_id": row["task_id"],
            "task_type": row["task_type"],
            "payload": json.loads(payload_json) if payload_json else {},
            "status": row["status"],
            "result": json.loads(result_json) if result_json else None,
            "error_message": row["error_message"],
            "attempts": int(row["attempts"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def _count_by_day(
        self,
        *,
        cursor: sqlite3.Cursor,
        table_name: str,
        since_iso: str,
    ) -> dict[str, int]:
        if table_name not in {"leads", "calls", "assessments"}:
            raise ValueError(f"Unsupported table for daily count: {table_name}")

        cursor.execute(
            f"""
            SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count
            FROM {table_name}
            WHERE created_at >= ?
            GROUP BY day
            """,
            (since_iso,),
        )
        return {row["day"]: int(row["count"]) for row in cursor.fetchall()}
