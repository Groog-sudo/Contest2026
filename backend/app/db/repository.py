from __future__ import annotations

import json
import sqlite3
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_now_dt() -> datetime:
    return datetime.now(timezone.utc)


class _ChromaKnowledgeStore:
    def __init__(self, settings: Settings) -> None:
        self.enabled = False
        self._collection = None

        if not settings.chroma_enabled:
            return

        try:
            import chromadb
        except Exception:
            return

        persist_dir = Path(settings.chroma_persist_directory).expanduser().resolve()
        persist_dir.mkdir(parents=True, exist_ok=True)
        try:
            client = chromadb.PersistentClient(path=str(persist_dir))
            self._collection = client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self.enabled = True
        except Exception:
            self.enabled = False
            self._collection = None

    def save(
        self,
        *,
        document_id: str,
        filename: str,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None:
        if not self.enabled or self._collection is None or not chunks:
            return

        ids = [f"{document_id}:{index}" for index in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "filename": filename,
                "title": filename,
                "chunk_index": index,
            }
            for index in range(len(chunks))
        ]

        try:
            self._collection.delete(where={"document_id": document_id})
        except Exception:
            pass

        self._collection.upsert(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def search(self, *, embedding: list[float], top_k: int) -> list[dict[str, object]]:
        if not self.enabled or self._collection is None:
            return []

        query = self._collection.query(
            query_embeddings=[embedding],
            n_results=max(1, top_k),
            include=["metadatas", "distances", "documents"],
        )
        ids = query.get("ids", [[]])
        metadatas = query.get("metadatas", [[]])
        distances = query.get("distances", [[]])
        documents = query.get("documents", [[]])

        id_items = ids[0] if ids else []
        metadata_items = metadatas[0] if metadatas else []
        distance_items = distances[0] if distances else []
        document_items = documents[0] if documents else []

        items: list[dict[str, object]] = []
        for index, chunk_id in enumerate(id_items):
            metadata = metadata_items[index] if index < len(metadata_items) else {}
            distance = distance_items[index] if index < len(distance_items) else None
            content = document_items[index] if index < len(document_items) else ""
            if not isinstance(metadata, dict):
                metadata = {}

            score: float | None = None
            if isinstance(distance, (int, float)):
                score = max(0.0, 1.0 - float(distance))

            items.append(
                {
                    "id": str(chunk_id),
                    "score": score,
                    "metadata": {
                        "document_id": metadata.get("document_id"),
                        "filename": metadata.get("filename") or "knowledge",
                        "title": metadata.get("title") or metadata.get("filename") or "knowledge",
                        "chunk_index": metadata.get("chunk_index"),
                        "text": str(content)[:900],
                    },
                }
            )
        return items


class DeliveryIssueRepository:
    def __init__(self, settings: Settings) -> None:
        self._knowledge_store = _ChromaKnowledgeStore(settings)
        if settings.database_backend == "postgresql":
            self._backend = _PostgresDeliveryIssueRepository(
                database_url=settings.database_url,
            )
        else:
            self._backend = _SQLiteDeliveryIssueRepository(db_path=settings.app_db_path)

    @property
    def supports_vector_search(self) -> bool:
        return self._knowledge_store.enabled

    def save_document_chunks(
        self,
        *,
        document_id: str,
        filename: str,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None:
        self._backend.save_document_chunks(
            document_id=document_id,
            filename=filename,
            chunks=chunks,
            embeddings=embeddings,
        )
        self._knowledge_store.save(
            document_id=document_id,
            filename=filename,
            chunks=chunks,
            embeddings=embeddings,
        )

    def search_knowledge_chunks(
        self,
        *,
        embedding: list[float],
        top_k: int,
    ) -> list[dict[str, object]]:
        return self._knowledge_store.search(embedding=embedding, top_k=top_k)

    def __getattr__(self, name: str):
        return getattr(self._backend, name)


class _SQLiteDeliveryIssueRepository:
    supports_vector_search = False

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
                    customer_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    incident_summary TEXT NOT NULL,
                    preferred_contact_time TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS calls (
                    call_id TEXT PRIMARY KEY,
                    lead_id TEXT NOT NULL,
                    incident_summary TEXT NOT NULL,
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
                CREATE TABLE IF NOT EXISTS incident_analyses (
                    analysis_id TEXT PRIMARY KEY,
                    lead_id TEXT NOT NULL,
                    primary_category TEXT NOT NULL,
                    severity_score INTEGER NOT NULL,
                    responsible_team TEXT NOT NULL,
                    analysis_json TEXT NOT NULL,
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
                CREATE TABLE IF NOT EXISTS knowledge_document_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    title TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(document_id, chunk_index)
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
            self._migrate_legacy_schema(connection=connection)
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

    def _table_columns(self, *, connection: sqlite3.Connection, table_name: str) -> set[str]:
        cursor = connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return {str(row[1]) for row in cursor.fetchall()}

    def _migrate_legacy_schema(self, *, connection: sqlite3.Connection) -> None:
        cursor = connection.cursor()

        lead_columns = self._table_columns(connection=connection, table_name="leads")
        if "customer_name" not in lead_columns and "student_name" in lead_columns:
            cursor.execute("ALTER TABLE leads RENAME TO leads_legacy")
            cursor.execute(
                """
                CREATE TABLE leads (
                    lead_id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    incident_summary TEXT NOT NULL,
                    preferred_contact_time TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO leads (
                    lead_id,
                    customer_name,
                    phone_number,
                    order_id,
                    incident_summary,
                    preferred_contact_time,
                    created_at
                )
                SELECT
                    lead_id,
                    student_name,
                    phone_number,
                    course_interest,
                    learning_goal,
                    preferred_call_time,
                    created_at
                FROM leads_legacy
                """
            )
            cursor.execute("DROP TABLE leads_legacy")

        call_columns = self._table_columns(connection=connection, table_name="calls")
        if "incident_summary" not in call_columns and "student_question" in call_columns:
            cursor.execute("ALTER TABLE calls RENAME TO calls_legacy")
            cursor.execute(
                """
                CREATE TABLE calls (
                    call_id TEXT PRIMARY KEY,
                    lead_id TEXT NOT NULL,
                    incident_summary TEXT NOT NULL,
                    status TEXT NOT NULL,
                    script_preview TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute(
                """
                INSERT INTO calls (
                    call_id,
                    lead_id,
                    incident_summary,
                    status,
                    script_preview,
                    created_at
                )
                SELECT
                    call_id,
                    lead_id,
                    student_question,
                    status,
                    script_preview,
                    created_at
                FROM calls_legacy
                """
            )
            cursor.execute("DROP TABLE calls_legacy")

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='assessments'"
        )
        has_legacy_assessments = cursor.fetchone() is not None
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='incident_analyses'"
        )
        has_incident_analyses = cursor.fetchone() is not None

        if has_legacy_assessments and has_incident_analyses:
            cursor.execute(
                """
                INSERT INTO incident_analyses (
                    analysis_id,
                    lead_id,
                    primary_category,
                    severity_score,
                    responsible_team,
                    analysis_json,
                    created_at
                )
                SELECT
                    assessment_id,
                    lead_id,
                    level,
                    score,
                    recommended_course,
                    rationale,
                    created_at
                FROM assessments
                WHERE assessment_id NOT IN (SELECT analysis_id FROM incident_analyses)
                """
            )
            cursor.execute("DROP TABLE assessments")

    def save_lead(
        self,
        *,
        lead_id: str,
        customer_name: str,
        phone_number: str,
        order_id: str,
        incident_summary: str,
        preferred_contact_time: str | None,
    ) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO leads (
                    lead_id,
                    customer_name,
                    phone_number,
                    order_id,
                    incident_summary,
                    preferred_contact_time,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead_id,
                    customer_name,
                    phone_number,
                    order_id,
                    incident_summary,
                    preferred_contact_time,
                    _utc_now(),
                ),
            )
            connection.commit()

    def get_lead(self, lead_id: str) -> dict[str, str] | None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT
                    lead_id,
                    customer_name,
                    phone_number,
                    order_id,
                    incident_summary
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
            "customer_name": row["customer_name"],
            "phone_number": row["phone_number"],
            "order_id": row["order_id"],
            "incident_summary": row["incident_summary"],
        }

    def save_call(
        self,
        *,
        call_id: str,
        lead_id: str,
        incident_summary: str,
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
                    incident_summary,
                    status,
                    script_preview,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    call_id,
                    lead_id,
                    incident_summary,
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

    def save_incident_analysis(
        self,
        *,
        analysis_id: str,
        lead_id: str,
        primary_category: str,
        severity_score: int,
        responsible_team: str,
        analysis_json: str,
    ) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO incident_analyses (
                    analysis_id,
                    lead_id,
                    primary_category,
                    severity_score,
                    responsible_team,
                    analysis_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    lead_id,
                    primary_category,
                    severity_score,
                    responsible_team,
                    analysis_json,
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

    def save_document_chunks(
        self,
        *,
        document_id: str,
        filename: str,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None:
        if not chunks:
            return

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM knowledge_document_chunks WHERE document_id = ?",
                (document_id,),
            )
            for index, chunk in enumerate(chunks):
                cursor.execute(
                    """
                    INSERT INTO knowledge_document_chunks (
                        chunk_id,
                        document_id,
                        filename,
                        title,
                        chunk_index,
                        content,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        f"{document_id}-{index}",
                        document_id,
                        filename,
                        filename,
                        index,
                        chunk,
                        _utc_now(),
                    ),
                )
            connection.commit()

    def search_knowledge_chunks(
        self,
        *,
        embedding: list[float],
        top_k: int,
    ) -> list[dict[str, object]]:
        return []

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

            cursor.execute("SELECT COUNT(DISTINCT lead_id) AS count FROM incident_analyses")
            leads_with_analyses = int(cursor.fetchone()["count"])

            cursor.execute("SELECT AVG(severity_score) AS avg_score FROM incident_analyses")
            avg_score_value = cursor.fetchone()["avg_score"]
            avg_severity_score = float(avg_score_value) if avg_score_value is not None else 0.0
            cursor.execute(
                "SELECT COUNT(*) AS count FROM incident_analyses WHERE severity_score >= 80"
            )
            high_risk_cases = int(cursor.fetchone()["count"])

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
            daily_incident_analyses = self._count_by_day(
                cursor=cursor,
                table_name="incident_analyses",
                since_iso=since_iso,
            )
            daily_high_risk = self._count_by_day(
                cursor=cursor,
                table_name="incident_analyses",
                since_iso=since_iso,
                where_clause="severity_score >= 80",
            )

        conversion_rate = (leads_with_calls / total_leads) if total_leads > 0 else 0.0
        completion_rate = (
            (leads_with_analyses / leads_with_calls) if leads_with_calls > 0 else 0.0
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
                    "analyses": daily_incident_analyses.get(date_key, 0),
                    "high_risk": daily_high_risk.get(date_key, 0),
                }
            )

        return {
            "total_leads": total_leads,
            "leads_with_calls": leads_with_calls,
            "leads_with_analyses": leads_with_analyses,
            "conversion_rate": conversion_rate,
            "resolution_rate": completion_rate,
            "avg_severity_score": avg_severity_score,
            "high_risk_cases": high_risk_cases,
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
        where_clause: str | None = None,
    ) -> dict[str, int]:
        if table_name not in {"leads", "calls", "incident_analyses"}:
            raise ValueError(f"Unsupported table for daily count: {table_name}")

        extra_filter = f"AND {where_clause}" if where_clause else ""
        cursor.execute(
            f"""
            SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count
            FROM {table_name}
            WHERE created_at >= ?
            {extra_filter}
            GROUP BY day
            """,
            (since_iso,),
        )
        return {row["day"]: int(row["count"]) for row in cursor.fetchall()}


class _PostgresDeliveryIssueRepository:
    supports_vector_search = False

    def __init__(self, *, database_url: str) -> None:
        self.database_url = database_url
        self._ensure_schema()

    def _connect(self):
        from psycopg import connect
        from psycopg.rows import dict_row

        return connect(self.database_url, row_factory=dict_row, connect_timeout=5)

    def _ensure_schema(self) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS leads (
                    lead_id TEXT PRIMARY KEY,
                    customer_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    order_id TEXT NOT NULL,
                    incident_summary TEXT NOT NULL,
                    preferred_contact_time TEXT,
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS calls (
                    call_id TEXT PRIMARY KEY,
                    lead_id TEXT NOT NULL,
                    incident_summary TEXT NOT NULL,
                    status TEXT NOT NULL,
                    script_preview TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
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
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS incident_analyses (
                    analysis_id TEXT PRIMARY KEY,
                    lead_id TEXT NOT NULL,
                    primary_category TEXT NOT NULL,
                    severity_score INTEGER NOT NULL,
                    responsible_team TEXT NOT NULL,
                    analysis_json TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL
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
                    created_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_document_chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    title TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL,
                    UNIQUE(document_id, chunk_index)
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
                    created_at TIMESTAMPTZ NOT NULL
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
                    created_at TIMESTAMPTZ NOT NULL,
                    updated_at TIMESTAMPTZ NOT NULL
                )
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_call_transcript_turns_lead_created_at
                ON call_transcript_turns (lead_id, created_at DESC, turn_index DESC)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_async_tasks_status_created_at
                ON async_tasks (status, created_at ASC)
                """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_knowledge_document_chunks_document
                ON knowledge_document_chunks (document_id, chunk_index)
                """
            )
            connection.commit()

    def save_lead(
        self,
        *,
        lead_id: str,
        customer_name: str,
        phone_number: str,
        order_id: str,
        incident_summary: str,
        preferred_contact_time: str | None,
    ) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO leads (
                    lead_id,
                    customer_name,
                    phone_number,
                    order_id,
                    incident_summary,
                    preferred_contact_time,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    lead_id,
                    customer_name,
                    phone_number,
                    order_id,
                    incident_summary,
                    preferred_contact_time,
                    _utc_now_dt(),
                ),
            )
            connection.commit()

    def get_lead(self, lead_id: str) -> dict[str, str] | None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                SELECT
                    lead_id,
                    customer_name,
                    phone_number,
                    order_id,
                    incident_summary
                FROM leads
                WHERE lead_id = %s
                """,
                (lead_id,),
            )
            row = cursor.fetchone()

        if row is None:
            return None

        return {
            "lead_id": row["lead_id"],
            "customer_name": row["customer_name"],
            "phone_number": row["phone_number"],
            "order_id": row["order_id"],
            "incident_summary": row["incident_summary"],
        }

    def save_call(
        self,
        *,
        call_id: str,
        lead_id: str,
        incident_summary: str,
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
                    incident_summary,
                    status,
                    script_preview,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    call_id,
                    lead_id,
                    incident_summary,
                    status,
                    script_preview,
                    _utc_now_dt(),
                ),
            )
            connection.commit()

    def call_exists(self, call_id: str) -> bool:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1 FROM calls WHERE call_id = %s LIMIT 1", (call_id,))
            return cursor.fetchone() is not None

    def save_transcript_turns(
        self,
        *,
        call_id: str,
        lead_id: str,
        turns: list[dict[str, str]],
    ) -> tuple[str, int]:
        transcript_id = str(uuid4())
        created_at = _utc_now_dt()

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
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
                WHERE lead_id = %s
                ORDER BY created_at DESC, turn_index DESC
                LIMIT %s
                """,
                (lead_id, limit),
            )
            rows = cursor.fetchall()

        return [{"speaker": row["speaker"], "utterance": row["utterance"]} for row in rows]

    def save_incident_analysis(
        self,
        *,
        analysis_id: str,
        lead_id: str,
        primary_category: str,
        severity_score: int,
        responsible_team: str,
        analysis_json: str,
    ) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO incident_analyses (
                    analysis_id,
                    lead_id,
                    primary_category,
                    severity_score,
                    responsible_team,
                    analysis_json,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    analysis_id,
                    lead_id,
                    primary_category,
                    severity_score,
                    responsible_team,
                    analysis_json,
                    _utc_now_dt(),
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
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (document_id, filename, status, chunk_count, _utc_now_dt()),
            )
            connection.commit()

    def save_document_chunks(
        self,
        *,
        document_id: str,
        filename: str,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None:
        if not chunks:
            return

        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM knowledge_document_chunks WHERE document_id = %s",
                (document_id,),
            )
            for index, chunk in enumerate(chunks):
                cursor.execute(
                    """
                    INSERT INTO knowledge_document_chunks (
                        chunk_id,
                        document_id,
                        filename,
                        title,
                        chunk_index,
                        content,
                        created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        f"{document_id}-{index}",
                        document_id,
                        filename,
                        filename,
                        index,
                        chunk,
                        _utc_now_dt(),
                    ),
                )
            connection.commit()

    def search_knowledge_chunks(
        self,
        *,
        embedding: list[float],
        top_k: int,
    ) -> list[dict[str, object]]:
        return []

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
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    recording_id,
                    call_id,
                    lead_id,
                    object_key,
                    content_type,
                    size_bytes,
                    _utc_now_dt(),
                ),
            )
            connection.commit()
        return recording_id

    def create_async_task(self, *, task_type: str, payload: dict[str, object]) -> str:
        task_id = str(uuid4())
        now = _utc_now_dt()
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
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                WHERE task_id = %s
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
                LIMIT %s
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
                WHERE status = %s
                ORDER BY created_at ASC
                LIMIT %s
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
                SET status = %s, attempts = attempts + 1, result_json = NULL, error_message = NULL, updated_at = %s
                WHERE task_id = %s
                """,
                ("processing", _utc_now_dt(), task_id),
            )
            connection.commit()

    def mark_task_done(self, *, task_id: str, result: dict[str, object]) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE async_tasks
                SET status = %s, result_json = %s, error_message = NULL, updated_at = %s
                WHERE task_id = %s
                """,
                ("done", json.dumps(result, ensure_ascii=False), _utc_now_dt(), task_id),
            )
            connection.commit()

    def mark_task_failed(self, *, task_id: str, error_message: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE async_tasks
                SET status = %s, error_message = %s, updated_at = %s
                WHERE task_id = %s
                """,
                ("failed", error_message, _utc_now_dt(), task_id),
            )
            connection.commit()

    def mark_task_requeued(self, *, task_id: str, error_message: str) -> None:
        with self._connect() as connection:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE async_tasks
                SET status = %s, error_message = %s, updated_at = %s
                WHERE task_id = %s
                """,
                ("queued", error_message, _utc_now_dt(), task_id),
            )
            connection.commit()

    def get_dashboard_metrics(
        self,
        *,
        period_days: int = 7,
    ) -> dict[str, float | int | list[dict[str, int | str]]]:
        today_utc = datetime.now(timezone.utc).date()
        period_start = today_utc - timedelta(days=period_days - 1)
        since_dt = datetime.combine(period_start, time.min, tzinfo=timezone.utc)

        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute("SELECT COUNT(*) AS count FROM leads")
            total_leads = int(cursor.fetchone()["count"])

            cursor.execute("SELECT COUNT(DISTINCT lead_id) AS count FROM calls")
            leads_with_calls = int(cursor.fetchone()["count"])

            cursor.execute("SELECT COUNT(DISTINCT lead_id) AS count FROM incident_analyses")
            leads_with_analyses = int(cursor.fetchone()["count"])

            cursor.execute("SELECT AVG(severity_score) AS avg_score FROM incident_analyses")
            avg_score_value = cursor.fetchone()["avg_score"]
            avg_severity_score = float(avg_score_value) if avg_score_value is not None else 0.0
            cursor.execute(
                "SELECT COUNT(*) AS count FROM incident_analyses WHERE severity_score >= 80"
            )
            high_risk_cases = int(cursor.fetchone()["count"])

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
                since_value=since_dt,
            )
            daily_calls = self._count_by_day(
                cursor=cursor,
                table_name="calls",
                since_value=since_dt,
            )
            daily_incident_analyses = self._count_by_day(
                cursor=cursor,
                table_name="incident_analyses",
                since_value=since_dt,
            )
            daily_high_risk = self._count_by_day(
                cursor=cursor,
                table_name="incident_analyses",
                since_value=since_dt,
                where_clause="severity_score >= 80",
            )

        conversion_rate = (leads_with_calls / total_leads) if total_leads > 0 else 0.0
        completion_rate = (
            (leads_with_analyses / leads_with_calls) if leads_with_calls > 0 else 0.0
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
                    "analyses": daily_incident_analyses.get(date_key, 0),
                    "high_risk": daily_high_risk.get(date_key, 0),
                }
            )

        return {
            "total_leads": total_leads,
            "leads_with_calls": leads_with_calls,
            "leads_with_analyses": leads_with_analyses,
            "conversion_rate": conversion_rate,
            "resolution_rate": completion_rate,
            "avg_severity_score": avg_severity_score,
            "high_risk_cases": high_risk_cases,
            "queued_tasks": task_counts.get("queued", 0),
            "processing_tasks": task_counts.get("processing", 0),
            "failed_tasks": task_counts.get("failed", 0),
            "period_days": period_days,
            "series": series,
        }

    def _task_row_to_dict(self, row: dict[str, object]) -> dict[str, object]:
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
            "created_at": row["created_at"].isoformat(),
            "updated_at": row["updated_at"].isoformat(),
        }

    def _count_by_day(
        self,
        *,
        cursor,
        table_name: str,
        since_value: datetime,
        where_clause: str | None = None,
    ) -> dict[str, int]:
        if table_name not in {"leads", "calls", "incident_analyses"}:
            raise ValueError(f"Unsupported table for daily count: {table_name}")

        extra_filter = f"AND {where_clause}" if where_clause else ""
        cursor.execute(
            f"""
            SELECT ((created_at AT TIME ZONE 'UTC')::date)::text AS day, COUNT(*) AS count
            FROM {table_name}
            WHERE created_at >= %s
            {extra_filter}
            GROUP BY day
            """,
            (since_value,),
        )
        return {row["day"]: int(row["count"]) for row in cursor.fetchall()}


