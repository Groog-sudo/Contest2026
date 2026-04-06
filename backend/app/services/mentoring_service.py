from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.clients.pinecone_client import PineconeClient
from app.clients.stt_client import STTClient
from app.clients.storage_client import ObjectStorageClient
from app.clients.tts_client import TTSClient
from app.core.config import Settings
from app.db.repository import MentoringRepository
from app.rag.chunker import split_text
from app.rag.loader import load_document
from app.schemas.assessment import LevelAssessmentRequest, LevelAssessmentResponse
from app.schemas.call import (
    CallRequest,
    CallRequestResponse,
    CallSourceItem,
    CallTranscriptIngestRequest,
    CallTranscriptIngestResponse,
    RecordingUploadResponse,
    TTSPreviewRequest,
    TTSPreviewResponse,
)
from app.schemas.dashboard import DashboardMetricsResponse
from app.schemas.lead import LeadRegistrationRequest, LeadRegistrationResponse
from app.schemas.queue import (
    QueueTaskItem,
    QueueTaskListResponse,
    QueueTaskProcessResponse,
    QueueWorkerRunResponse,
)


class MentoringService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repository = MentoringRepository(settings.app_db_path)
        self.stt_client = STTClient(settings)
        self.tts_client = TTSClient(settings)
        self.pinecone_client = PineconeClient(settings)
        self.storage_client = ObjectStorageClient(settings)

    def register_lead(self, payload: LeadRegistrationRequest) -> LeadRegistrationResponse:
        lead_id = str(uuid4())
        self.repository.save_lead(
            lead_id=lead_id,
            student_name=payload.student_name,
            phone_number=payload.phone_number,
            course_interest=payload.course_interest,
            learning_goal=payload.learning_goal,
            preferred_call_time=payload.preferred_call_time,
        )
        next_action = (
            f"{payload.student_name} 님 상담 정보를 접수했습니다. "
            "이제 AI 멘토링 콜 요청을 생성해 연락 흐름을 이어갈 수 있습니다."
        )
        return LeadRegistrationResponse(
            lead_id=lead_id,
            status="captured",
            next_action=next_action,
        )

    def create_call_request(self, payload: CallRequest) -> CallRequestResponse:
        call_id = str(uuid4())
        lead = self.repository.get_lead(payload.lead_id)

        if self.settings.rag_configured and self.settings.outbound_call_configured:
            status = "queued"
            next_step = "하이브리드 RAG 근거를 바탕으로 아웃바운드 콜 큐에 등록합니다."
        elif self.settings.rag_configured:
            status = "script_ready"
            next_step = "RAG 기반 스크립트가 준비되었습니다. 통신 연동 후 자동 발신을 연결하세요."
        else:
            status = "drafted"
            next_step = "현재는 지식베이스 미연동 상태로 기본 상담 스크립트 초안을 제공합니다."

        sources = self._build_sources(payload=payload)
        script_preview = self._build_script_preview(
            payload=payload,
            status=status,
            lead=lead,
            sources=sources,
        )
        self.repository.save_call(
            call_id=call_id,
            lead_id=payload.lead_id,
            student_question=payload.student_question,
            status=status,
            script_preview=script_preview,
        )

        return CallRequestResponse(
            call_id=call_id,
            status=status,
            script_preview=script_preview,
            sources=sources,
            next_step=next_step,
        )

    async def ingest(self, file: UploadFile) -> dict[str, str]:
        document_id = str(uuid4())
        filename = file.filename or "unknown"
        text = await load_document(file)
        chunks = split_text(text=text, chunk_size=700)
        status = "knowledge_base_pending"

        if self.settings.rag_configured and chunks:
            try:
                vectors = self._build_pinecone_vectors(
                    document_id=document_id,
                    filename=filename,
                    chunks=chunks,
                )
                self.pinecone_client.upsert_chunks(vectors=vectors)
                status = "accepted"
            except Exception:
                status = "knowledge_base_pending"

        self.repository.save_document(
            document_id=document_id,
            filename=filename,
            status=status,
            chunk_count=len(chunks),
        )
        return {"document_id": document_id, "status": status}

    def ingest_call_transcript(self, payload: CallTranscriptIngestRequest) -> CallTranscriptIngestResponse:
        turns = self._resolve_turns(payload)
        transcript_id, saved_turns = self.repository.save_transcript_turns(
            call_id=payload.call_id,
            lead_id=payload.lead_id,
            turns=turns,
        )
        summary = self._summarize_turns(turns)
        return CallTranscriptIngestResponse(
            transcript_id=transcript_id,
            status="stored",
            saved_turns=saved_turns,
            summary=summary,
        )

    async def upload_recording_and_enqueue(
        self,
        *,
        file: UploadFile,
        call_id: str,
        lead_id: str,
    ) -> RecordingUploadResponse:
        filename = file.filename or "recording.wav"
        content_type = file.content_type or "audio/wav"
        blob = await file.read()
        await file.close()

        object_key = self._recording_object_key(
            lead_id=lead_id,
            call_id=call_id,
            filename=filename,
        )
        stored = self.storage_client.put_bytes(
            key=object_key,
            data=blob,
            content_type=content_type,
        )
        recording_id = self.repository.save_recording(
            call_id=call_id,
            lead_id=lead_id,
            object_key=stored.key,
            content_type=stored.content_type,
            size_bytes=stored.size,
        )
        queue_task_id = self.repository.create_async_task(
            task_type="stt_transcription",
            payload={
                "recording_id": recording_id,
                "call_id": call_id,
                "lead_id": lead_id,
                "object_key": stored.key,
                "content_type": content_type,
                "filename": filename,
            },
        )
        return RecordingUploadResponse(
            recording_id=recording_id,
            status="queued",
            object_key=stored.key,
            storage_url=stored.url,
            queue_task_id=queue_task_id,
        )

    def create_tts_preview(self, payload: TTSPreviewRequest) -> TTSPreviewResponse:
        audio_bytes, mime_type = self.tts_client.synthesize(
            script=payload.script,
            voice=payload.voice,
        )
        object_key = f"tts-previews/{uuid4()}.mp3"
        stored = self.storage_client.put_bytes(
            key=object_key,
            data=audio_bytes,
            content_type=mime_type,
        )
        return TTSPreviewResponse(
            status="generated",
            provider=self.tts_client.provider_name,
            voice=payload.voice,
            audio_url=stored.url,
            mime_type=mime_type,
        )

    def evaluate_level(self, payload: LevelAssessmentRequest) -> LevelAssessmentResponse:
        total = sum(answer.score for answer in payload.answers)
        max_total = len(payload.answers) * 5
        normalized_score = round((total / max_total) * 100)
        level = self._score_to_level(normalized_score)
        recommended_course = self._course_by_level(level)
        assessment_id = str(uuid4())

        memory = self.repository.list_recent_utterances(lead_id=payload.lead_id, limit=3)
        mentoring_plan = self._build_mentoring_plan(
            level=level,
            recommended_course=recommended_course,
            memory=memory,
        )
        rag_context_ids = ["curriculum-catalog", f"lead:{payload.lead_id}"]
        if memory:
            rag_context_ids.append("call-memory")

        self.repository.save_assessment(
            assessment_id=assessment_id,
            lead_id=payload.lead_id,
            level=level,
            score=normalized_score,
            recommended_course=recommended_course,
            rationale=mentoring_plan,
        )

        return LevelAssessmentResponse(
            assessment_id=assessment_id,
            level=level,
            score=normalized_score,
            recommended_course=recommended_course,
            mentoring_plan=mentoring_plan,
            rag_context_ids=rag_context_ids,
        )

    def list_queue_tasks(self) -> QueueTaskListResponse:
        items = [
            QueueTaskItem(**item)
            for item in self.repository.list_async_tasks(limit=30)
        ]
        return QueueTaskListResponse(items=items)

    def process_queue_task(self, task_id: str) -> QueueTaskProcessResponse:
        task = self.repository.get_async_task(task_id)
        if task is None:
            return QueueTaskProcessResponse(
                task_id=task_id,
                status="failed",
                error_message="Queue task not found.",
            )

        status = str(task.get("status", "queued"))
        attempts = int(task.get("attempts", 0))

        if status == "done":
            completed_result = task.get("result")
            return QueueTaskProcessResponse(
                task_id=task_id,
                status="done",
                result=completed_result if isinstance(completed_result, dict) else None,
            )
        if status == "processing":
            return QueueTaskProcessResponse(
                task_id=task_id,
                status="failed",
                error_message="Queue task is already being processed.",
            )

        if attempts >= self.settings.queue_max_attempts:
            error_message = (
                f"Queue task reached max attempts ({self.settings.queue_max_attempts})."
            )
            self.repository.mark_task_failed(task_id=task_id, error_message=error_message)
            return QueueTaskProcessResponse(
                task_id=task_id,
                status="failed",
                error_message=error_message,
            )

        self.repository.mark_task_processing(task_id=task_id)
        try:
            result = self._execute_task(task=task)
            self.repository.mark_task_done(task_id=task_id, result=result)
            return QueueTaskProcessResponse(
                task_id=task_id,
                status="done",
                result=result,
            )
        except Exception as exc:
            error_message = str(exc)
            retry_queued = (attempts + 1) < self.settings.queue_max_attempts
            if retry_queued:
                self.repository.mark_task_requeued(
                    task_id=task_id,
                    error_message=error_message,
                )
            else:
                self.repository.mark_task_failed(
                    task_id=task_id,
                    error_message=error_message,
                )
            return QueueTaskProcessResponse(
                task_id=task_id,
                status="failed",
                error_message=error_message,
                retry_queued=retry_queued,
            )

    def process_pending_queue_tasks(self, *, limit: int = 10) -> QueueWorkerRunResponse:
        tasks = self.repository.list_queued_tasks_for_worker(limit=limit)
        processed = 0
        succeeded = 0
        failed = 0
        requeued = 0

        for task in tasks:
            processed += 1
            task_id = str(task.get("task_id"))
            response = self.process_queue_task(task_id)
            if response.status == "done":
                succeeded += 1
            elif response.retry_queued:
                requeued += 1
            else:
                failed += 1

        return QueueWorkerRunResponse(
            requested_limit=limit,
            processed=processed,
            succeeded=succeeded,
            failed=failed,
            requeued=requeued,
        )

    def get_dashboard_metrics(self, *, period_days: int = 7) -> DashboardMetricsResponse:
        metrics = self.repository.get_dashboard_metrics(period_days=period_days)
        return DashboardMetricsResponse(**metrics)

    def _execute_task(self, *, task: dict[str, object]) -> dict[str, object]:
        task_type = task["task_type"]
        payload = task["payload"]
        if not isinstance(payload, dict):
            raise RuntimeError("Invalid task payload.")

        if task_type == "stt_transcription":
            return self._process_stt_task(payload=payload)

        raise RuntimeError(f"Unsupported task type: {task_type}")

    def _process_stt_task(self, *, payload: dict[str, object]) -> dict[str, object]:
        object_key = str(payload.get("object_key", ""))
        call_id = str(payload.get("call_id", ""))
        lead_id = str(payload.get("lead_id", ""))
        filename = str(payload.get("filename", "recording.wav"))

        if not object_key or not call_id or not lead_id:
            raise RuntimeError("STT task payload is missing required fields.")

        blob = self.storage_client.get_bytes(key=object_key)
        transcript_text = self.stt_client.transcribe(
            audio_bytes=blob,
            filename=filename,
        )
        turns = self._parse_transcript_text(transcript_text)
        transcript_id, saved_turns = self.repository.save_transcript_turns(
            call_id=call_id,
            lead_id=lead_id,
            turns=turns,
        )
        summary = self._summarize_turns(turns)
        return {
            "transcript_id": transcript_id,
            "saved_turns": saved_turns,
            "summary": summary,
        }

    def _build_script_preview(
        self,
        payload: CallRequest,
        *,
        status: str,
        lead: dict[str, str] | None,
        sources: list[CallSourceItem],
    ) -> str:
        learning_goal = lead["learning_goal"] if lead else "학습 목표를 재확인합니다."
        source_hint = sources[0].title if sources else "초기 상담 정보"
        opening = (
            f"안녕하세요, {payload.student_name} 님. 남겨주신 {payload.course_interest} 문의를 보고 "
            "AI 멘토가 전화드렸습니다."
        )
        need = (
            f"핵심 질문은 '{payload.student_question}'로 이해했습니다. "
            "목표와 현재 수준을 확인하고 가장 적합한 과정을 제안드리겠습니다."
        )
        guidance = (
            f"현재 목표는 '{learning_goal}'이며, 우선 근거 자료 '{source_hint}'를 기준으로 설명드립니다."
        )
        closing = {
            "queued": "통화 종료 후 상담 요약과 추천 과정을 CRM에 자동 기록합니다.",
            "script_ready": "스크립트는 준비되었으며 상담원이 검토 후 즉시 활용할 수 있습니다.",
            "drafted": "지식베이스 연결 전이라 상담 메모리 중심 초안을 제공합니다.",
        }[status]
        return " ".join([opening, need, guidance, closing])

    def _build_sources(self, *, payload: CallRequest) -> list[CallSourceItem]:
        sources: list[CallSourceItem] = []

        recent_utterances = self.repository.list_recent_utterances(lead_id=payload.lead_id, limit=3)
        for index, memory in enumerate(recent_utterances, start=1):
            text = memory["utterance"][:50]
            sources.append(
                CallSourceItem(
                    id=f"call-memory-{index}",
                    title=f"상담 이력 메모리: {text}",
                    score=0.7,
                )
            )

        curriculum_sources = self._search_curriculum_sources(
            question=payload.student_question,
            top_k=payload.top_k,
        )
        sources.extend(curriculum_sources)

        if not sources:
            sources.append(
                CallSourceItem(
                    id="intake-form",
                    title="수강생 상담 신청서 기반 초안",
                    score=None,
                )
            )

        return sources

    def _search_curriculum_sources(self, *, question: str, top_k: int) -> list[CallSourceItem]:
        if not self.settings.rag_configured:
            return []

        try:
            vector = self._embed_texts([question])[0]
            matches = self.pinecone_client.query(vector=vector, top_k=top_k)
        except Exception:
            return []

        sources: list[CallSourceItem] = []
        for match in matches:
            metadata = match.get("metadata", {}) if isinstance(match, dict) else {}
            if not isinstance(metadata, dict):
                metadata = {}
            title = (
                str(metadata.get("title") or metadata.get("filename") or "커리큘럼 문서 근거")
            )
            score_value = match.get("score") if isinstance(match, dict) else None
            score = float(score_value) if isinstance(score_value, (int, float)) else None
            sources.append(
                CallSourceItem(
                    id=str(match.get("id", "curriculum-source")),
                    title=title,
                    score=score,
                )
            )
        return sources

    def _build_pinecone_vectors(
        self,
        *,
        document_id: str,
        filename: str,
        chunks: list[str],
    ) -> list[dict[str, object]]:
        embeddings = self._embed_texts(chunks)
        vectors: list[dict[str, object]] = []
        for index, chunk in enumerate(chunks):
            vectors.append(
                {
                    "id": f"{document_id}-{index}",
                    "values": embeddings[index],
                    "metadata": {
                        "document_id": document_id,
                        "filename": filename,
                        "title": filename,
                        "chunk_index": index,
                        "text": chunk[:900],
                    },
                }
            )
        return vectors

    def _embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required for embedding.")

        from openai import OpenAI

        client = OpenAI(api_key=self.settings.openai_api_key)
        vectors: list[list[float]] = []
        for text in texts:
            response = client.embeddings.create(
                model=self.settings.openai_embedding_model,
                input=text,
            )
            vectors.append(response.data[0].embedding)
        return vectors

    def _resolve_turns(self, payload: CallTranscriptIngestRequest) -> list[dict[str, str]]:
        if payload.turns:
            return [
                {"speaker": turn.speaker, "utterance": turn.utterance.strip()}
                for turn in payload.turns
                if turn.utterance.strip()
            ]

        raw_text = payload.transcript_text
        if raw_text is None and payload.recording_url:
            raw_text = self.stt_client.transcribe(recording_url=payload.recording_url)

        if raw_text is None:
            return [{"speaker": "student", "utterance": "전사 데이터 없음"}]

        return self._parse_transcript_text(raw_text)

    def _parse_transcript_text(self, transcript_text: str) -> list[dict[str, str]]:
        turns: list[dict[str, str]] = []
        for line in transcript_text.splitlines():
            candidate = line.strip()
            if not candidate:
                continue

            if ":" in candidate:
                prefix, message = candidate.split(":", 1)
                speaker = prefix.strip().lower()
                normalized_speaker = speaker if speaker in {"student", "ai", "counselor"} else "student"
                utterance = message.strip()
            else:
                normalized_speaker = "student"
                utterance = candidate

            if utterance:
                turns.append({"speaker": normalized_speaker, "utterance": utterance})

        if not turns:
            turns.append({"speaker": "student", "utterance": transcript_text.strip()})

        return turns

    def _summarize_turns(self, turns: list[dict[str, str]]) -> str:
        student_lines = [turn["utterance"] for turn in turns if turn["speaker"] == "student"]
        ai_lines = [turn["utterance"] for turn in turns if turn["speaker"] == "ai"]

        student_focus = student_lines[0] if student_lines else "학습 목표 확인 필요"
        ai_focus = ai_lines[0] if ai_lines else "다음 통화에서 레벨 테스트를 진행합니다."
        return f"수강생 핵심 요청: {student_focus} / 상담 가이드: {ai_focus}"

    def _score_to_level(self, score: int) -> str:
        if score < 40:
            return "beginner"
        if score < 70:
            return "intermediate"
        return "advanced"

    def _course_by_level(self, level: str) -> str:
        mapping = {
            "beginner": "AI 기초 트랙 (파이썬/데이터 리터러시)",
            "intermediate": "AI 실무 트랙 (프로젝트 중심 부트캠프)",
            "advanced": "AI 고급 트랙 (LLM 서비스/배포 심화)",
        }
        return mapping[level]

    def _build_mentoring_plan(
        self,
        *,
        level: str,
        recommended_course: str,
        memory: list[dict[str, str]],
    ) -> str:
        memory_hint = memory[0]["utterance"] if memory else "초기 상담 기록이 아직 없습니다."
        return (
            f"레벨 판정은 {level}이며 추천 과정은 '{recommended_course}'입니다. "
            f"최근 상담 메모리 기준 핵심 요구는 '{memory_hint[:80]}'로 파악되었습니다. "
            "1주 단위 학습 목표를 설정하고 다음 상담에서 성취도를 재평가합니다."
        )

    def _recording_object_key(self, *, lead_id: str, call_id: str, filename: str) -> str:
        extension = Path(filename).suffix or ".wav"
        return f"recordings/{lead_id}/{call_id}/{uuid4()}{extension}"
