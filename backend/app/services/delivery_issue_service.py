
from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.clients.stt_client import STTClient
from app.clients.storage_client import ObjectStorageClient
from app.clients.tts_client import TTSClient
from app.core.config import Settings
from app.db.repository import DeliveryIssueRepository
from app.rag.chunker import split_text
from app.rag.loader import load_document
from app.schemas.assessment import (
    FeedbackMessage,
    IncidentAnalysisRequest,
    IncidentAnalysisResponse,
    IssueDetails,
    OrderInfo,
)
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


class DeliveryIssueService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repository = DeliveryIssueRepository(settings)
        self.stt_client = STTClient(settings)
        self.tts_client = TTSClient(settings)
        self.storage_client = ObjectStorageClient(settings)

    def register_lead(self, payload: LeadRegistrationRequest) -> LeadRegistrationResponse:
        lead_id = str(uuid4())
        incident_summary = payload.incident_summary
        if payload.order_items:
            incident_summary += f" / 주문메뉴: {', '.join(payload.order_items)}"
        if payload.requested_resolution:
            incident_summary += f" / 요청조치: {payload.requested_resolution}"

        self.repository.save_lead(
            lead_id=lead_id,
            customer_name=payload.customer_name,
            phone_number=payload.phone_number,
            order_id=payload.order_id or "order-unknown",
            incident_summary=incident_summary,
            preferred_contact_time=payload.preferred_contact_time,
        )
        next_action = (
            f"{payload.customer_name} 님의 배달 불만 접수를 완료했습니다. "
            "이제 상담 콜 요청을 생성해 문제 분류/담당 주체 판정 단계로 진행할 수 있습니다."
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
            next_step = "불만 분류용 상담 스크립트를 바탕으로 아웃바운드 콜 큐에 등록합니다."
        elif self.settings.rag_configured:
            status = "script_ready"
            next_step = "RAG 기반 상담 스크립트가 준비되었습니다. 통신 연동 후 자동 발신을 연결하세요."
        else:
            status = "drafted"
            next_step = "기본 상담 스크립트 초안을 생성했습니다. 지식베이스 연결 시 정확도가 향상됩니다."

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
            incident_summary=payload.incident_summary,
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

        if self.settings.rag_configured and self.repository.supports_vector_search and chunks:
            try:
                embeddings = self._embed_texts(chunks)
                self.repository.save_document_chunks(
                    document_id=document_id,
                    filename=filename,
                    chunks=chunks,
                    embeddings=embeddings,
                )
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

    def analyze_incident(self, payload: IncidentAnalysisRequest) -> IncidentAnalysisResponse:
        lead = self.repository.get_lead(payload.lead_id)
        narrative = self._compose_narrative(payload=payload, lead=lead)

        classification = self._classify_issue(narrative)
        requested_resolution = self._resolve_requested_resolution(
            narrative=narrative,
            explicit_requests=list(payload.requested_resolution),
        )
        follow_up_questions = self._build_follow_up_questions(
            payload=payload,
            classification=classification,
            narrative=narrative,
        )

        order_id = payload.order_id or (lead.get("order_id") if isinstance(lead, dict) else None)
        lead_items = self._extract_items_from_lead(lead)
        order_items = payload.order_items or lead_items

        issue_details = IssueDetails(
            reported_problem=narrative[:700],
            evidence_available=payload.evidence_available,
            missing_items=self._extract_keyword_items(narrative, keyword="누락"),
            wrong_items=self._extract_keyword_items(narrative, keyword="잘못"),
            foreign_object_reported="foreign_object" in classification["subcategories"],
            allergy_or_health_risk=classification["safety_flag"],
            delivery_delay_minutes=self._extract_delay_minutes(narrative),
            package_damage=any(
                keyword in narrative
                for keyword in ["파손", "찌그러", "훼손", "쏟아", "샜", "샘"]
            ),
        )

        summary_for_customer = (
            "말씀해 주신 내용을 정리하면, "
            f"{classification['summary_fragment']}이며 "
            f"{self._responsible_party_label(classification['responsible_parties'])} 확인이 필요한 상황입니다. "
            "요청하신 조치 내용까지 포함해 접수하겠습니다."
        )
        incident_overview = (
            f"고객은 '{narrative[:120]}' 이슈를 신고했습니다. "
            f"분류 결과는 {classification['primary_category']}이며 세부 유형은 {', '.join(classification['subcategories']) or '미확정'}입니다. "
            f"심각도는 {classification['severity']}로 판정되며, "
            f"안전 플래그는 {'활성화' if classification['safety_flag'] else '비활성화'}되었습니다."
        )

        merchant_feedback = self._build_feedback_message(
            channel="merchant",
            send="merchant" in classification["responsible_parties"],
            order_id=order_id,
            narrative=narrative,
            requested_resolution=requested_resolution,
            safety_flag=classification["safety_flag"],
        )
        delivery_feedback = self._build_feedback_message(
            channel="delivery_provider",
            send="delivery_provider" in classification["responsible_parties"],
            order_id=order_id,
            narrative=narrative,
            requested_resolution=requested_resolution,
            safety_flag=classification["safety_flag"],
        )
        platform_feedback = self._build_feedback_message(
            channel="platform",
            send="platform" in classification["responsible_parties"],
            order_id=order_id,
            narrative=narrative,
            requested_resolution=requested_resolution,
            safety_flag=classification["safety_flag"],
        )

        response = IncidentAnalysisResponse(
            summary_for_customer=summary_for_customer,
            incident_overview=incident_overview,
            primary_category=classification["primary_category"],
            subcategories=classification["subcategories"],
            responsible_parties=classification["responsible_parties"],
            severity=classification["severity"],
            safety_flag=classification["safety_flag"],
            refund_request="refund" in requested_resolution,
            redelivery_request="redelivery" in requested_resolution,
            recook_request="recook" in requested_resolution,
            customer_emotion=classification["customer_emotion"],
            order_info=OrderInfo(
                order_id=order_id,
                items=order_items,
                ordered_at=payload.ordered_at,
                delivered_at=payload.delivered_at,
            ),
            issue_details=issue_details,
            customer_requested_resolution=requested_resolution,
            follow_up_questions_needed=follow_up_questions,
            merchant_feedback=merchant_feedback,
            delivery_feedback=delivery_feedback,
            platform_feedback=platform_feedback,
            internal_review_note=self._build_internal_review_note(
                classification=classification,
                follow_up_questions=follow_up_questions,
            ),
        )

        analysis_id = str(uuid4())
        severity_score = {"low": 25, "medium": 55, "high": 80, "critical": 95}[response.severity]
        self.repository.save_incident_analysis(
            analysis_id=analysis_id,
            lead_id=payload.lead_id,
            primary_category=response.primary_category,
            severity_score=severity_score,
            responsible_team=", ".join(response.responsible_parties),
            analysis_json=json.dumps(response.model_dump(), ensure_ascii=False),
        )

        return response

    def list_queue_tasks(self) -> QueueTaskListResponse:
        items = [QueueTaskItem(**item) for item in self.repository.list_async_tasks(limit=30)]
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
            error_message = f"Queue task reached max attempts ({self.settings.queue_max_attempts})."
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
                self.repository.mark_task_requeued(task_id=task_id, error_message=error_message)
            else:
                self.repository.mark_task_failed(task_id=task_id, error_message=error_message)
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
        leads_with_analyses = int(metrics.get("leads_with_analyses", 0))
        resolution_rate = float(metrics.get("resolution_rate", 0.0))
        high_risk_cases = int(metrics.get("high_risk_cases", 0))

        raw_series = metrics.get("series", [])
        series = [
            {
                "date": point.get("date", ""),
                "leads": int(point.get("leads", 0)),
                "calls": int(point.get("calls", 0)),
                "analyses": int(point.get("analyses", point.get("incident_analyses", 0))),
                "high_risk": int(point.get("high_risk", 0)),
            }
            for point in raw_series
        ]

        return DashboardMetricsResponse(
            total_leads=int(metrics.get("total_leads", 0)),
            leads_with_calls=int(metrics.get("leads_with_calls", 0)),
            leads_with_analyses=leads_with_analyses,
            conversion_rate=float(metrics.get("conversion_rate", 0.0)),
            resolution_rate=resolution_rate,
            high_risk_cases=high_risk_cases,
            queued_tasks=int(metrics.get("queued_tasks", 0)),
            processing_tasks=int(metrics.get("processing_tasks", 0)),
            failed_tasks=int(metrics.get("failed_tasks", 0)),
            period_days=int(metrics.get("period_days", period_days)),
            series=series,
        )

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
        transcript_text = self.stt_client.transcribe(audio_bytes=blob, filename=filename)
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
        source_hint = sources[0].title if sources else "초기 접수 정보"
        preserved_incident = lead["incident_summary"] if lead else payload.incident_summary
        requested_resolution = payload.requested_resolution or "요청 조치 미지정"
        opening = (
            f"안녕하세요, {payload.customer_name} 님. 배달 주문 불편 사항 접수를 도와드리겠습니다. "
            "불편을 겪으셔서 정말 죄송합니다."
        )
        need = (
            f"현재 접수된 핵심 내용은 '{payload.incident_summary}'입니다. "
            f"요청하신 조치는 '{requested_resolution}'로 확인했습니다."
        )
        guidance = (
            f"추가 확인은 한 번에 하나씩 진행하고, 근거 자료 '{source_hint}' 및 "
            f"기존 접수 메모 '{preserved_incident[:80]}'를 함께 참고합니다."
        )
        closing = {
            "queued": "상담 종료 후 분류 JSON과 피드백 문안을 담당 주체별로 자동 전달합니다.",
            "script_ready": "스크립트가 준비되었습니다. 상담원이 검토 후 즉시 활용할 수 있습니다.",
            "drafted": "지식베이스 연결 전이라 접수 메모 중심의 기본 스크립트를 제공합니다.",
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
                    title=f"이전 상담 메모리: {text}",
                    score=0.7,
                )
            )

        knowledge_sources = self._search_knowledge_sources(
            question=payload.incident_summary,
            top_k=payload.top_k,
        )
        sources.extend(knowledge_sources)

        if not sources:
            sources.append(
                CallSourceItem(
                    id="intake-form",
                    title="초기 불만 접수서 기반 초안",
                    score=None,
                )
            )

        return sources

    def _search_knowledge_sources(self, *, question: str, top_k: int) -> list[CallSourceItem]:
        if not self.settings.rag_configured or not self.repository.supports_vector_search:
            return []

        try:
            vector = self._embed_texts([question])[0]
            matches = self.repository.search_knowledge_chunks(
                embedding=vector,
                top_k=top_k,
            )
        except Exception:
            return []

        sources: list[CallSourceItem] = []
        for match in matches:
            metadata = match.get("metadata", {}) if isinstance(match, dict) else {}
            if not isinstance(metadata, dict):
                metadata = {}
            title = str(metadata.get("title") or metadata.get("filename") or "운영 가이드 문서")
            score_value = match.get("score") if isinstance(match, dict) else None
            score = float(score_value) if isinstance(score_value, (int, float)) else None
            sources.append(
                CallSourceItem(
                    id=str(match.get("id", "knowledge-source")),
                    title=title,
                    score=score,
                )
            )
        return sources

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
            return [{"speaker": "customer", "utterance": "전사 데이터 없음"}]

        return self._parse_transcript_text(raw_text)

    def _parse_transcript_text(self, transcript_text: str) -> list[dict[str, str]]:
        turns: list[dict[str, str]] = []
        speaker_alias = {
            "student": "customer",
            "customer": "customer",
            "user": "customer",
            "mentor": "ai",
            "agent": "ai",
            "ai": "ai",
            "counselor": "counselor",
        }
        for line in transcript_text.splitlines():
            candidate = line.strip()
            if not candidate:
                continue

            if ":" in candidate:
                prefix, message = candidate.split(":", 1)
                speaker = prefix.strip().lower()
                normalized_speaker = speaker_alias.get(speaker, "customer")
                utterance = message.strip()
            else:
                normalized_speaker = "customer"
                utterance = candidate

            if utterance:
                turns.append({"speaker": normalized_speaker, "utterance": utterance})

        if not turns:
            turns.append({"speaker": "customer", "utterance": transcript_text.strip()})

        return turns

    def _summarize_turns(self, turns: list[dict[str, str]]) -> str:
        customer_lines = [turn["utterance"] for turn in turns if turn["speaker"] == "customer"]
        ai_lines = [turn["utterance"] for turn in turns if turn["speaker"] == "ai"]

        customer_focus = customer_lines[0] if customer_lines else "핵심 이슈 확인 필요"
        ai_focus = ai_lines[0] if ai_lines else "추가 확인 질문 후 분류를 진행합니다."
        return f"고객 핵심 이슈: {customer_focus} / 상담사 응대: {ai_focus}"

    def _compose_narrative(
        self,
        *,
        payload: IncidentAnalysisRequest,
        lead: dict[str, object] | None,
    ) -> str:
        parts: list[str] = []
        if payload.customer_message:
            parts.append(payload.customer_message)
        if payload.transcript_text:
            parts.append(payload.transcript_text)
        if isinstance(lead, dict):
            lead_summary = str(lead.get("incident_summary") or "").strip()
            if lead_summary:
                parts.append(lead_summary)
        if not parts:
            return "고객 이슈 설명 없음"
        return " ".join(parts).lower()

    def _classify_issue(self, narrative: str) -> dict[str, object]:
        merchant_subcategories: list[str] = []
        delivery_subcategories: list[str] = []
        platform_subcategories: list[str] = []

        if self._contains_any(narrative, ["이물", "머리카락", "벌레", "금속", "플라스틱"]):
            merchant_subcategories.extend(["foreign_object", "hygiene_issue"])
        if self._contains_any(narrative, ["잘못된 메뉴", "다른 메뉴", "오배송 메뉴", "떡볶이가 왔", "메뉴가 달라"]):
            merchant_subcategories.append("wrong_menu")
        if self._contains_any(narrative, ["누락", "빠졌", "안 왔", "없었"]):
            merchant_subcategories.append("missing_item")
        if self._contains_any(narrative, ["상했", "냄새", "덜 익", "탄", "맛이 이상", "식중독", "차가워"]):
            merchant_subcategories.append("food_quality_issue")
        if self._contains_any(narrative, ["양이 적", "양이 너무"]):
            merchant_subcategories.append("portion_issue")
        if self._contains_any(narrative, ["포장 불량", "봉인 불량", "포장이 약"]):
            merchant_subcategories.append("packaging_issue_merchant")
        if self._contains_any(narrative, ["알레르기", "알러지", "재료 표기", "견과", "갑각류"]):
            merchant_subcategories.append("allergy_risk")
        if self._contains_any(narrative, ["위생", "비위생", "더러", "청결"]):
            merchant_subcategories.append("hygiene_issue")

        if self._contains_any(narrative, ["배달 지연", "늦게", "예정 시간보다", "한참 뒤", "1시간 넘"]):
            delivery_subcategories.append("late_delivery")
        if self._contains_any(narrative, ["쏟아", "흘러", "국물이 샜"]):
            delivery_subcategories.append("spilled_during_delivery")
        if self._contains_any(narrative, ["포장 파손", "박스 파손", "봉투 찢"]):
            delivery_subcategories.append("damaged_package_delivery")
        if self._contains_any(narrative, ["오배송", "다른 주소", "다른 집", "다른 고객"]):
            delivery_subcategories.append("rider_misdelivery")
        if self._contains_any(narrative, ["배달 완료인데 못 받", "미수령", "도착 안 했"]):
            delivery_subcategories.append("no_delivery_received")
        if self._contains_any(narrative, ["막 던", "거칠게", "취급 부주의"]):
            delivery_subcategories.append("poor_delivery_handling")
        if self._contains_any(narrative, ["식어서", "온도", "차갑게 도착"]):
            delivery_subcategories.append("temperature_drop_due_to_delay")

        if self._contains_any(narrative, ["결제 오류", "결제됐는데", "중복 결제", "승인 실패"]):
            platform_subcategories.append("payment_issue")
        if self._contains_any(narrative, ["앱 주문 정보", "시스템 불일치", "주문이 안 들어", "앱에는"]):
            platform_subcategories.append("app_order_mismatch")
        if self._contains_any(narrative, ["중복 주문"]):
            platform_subcategories.append("duplicate_order")
        if self._contains_any(narrative, ["쿠폰", "프로모션", "할인 적용"]):
            platform_subcategories.append("coupon_promotion_issue")
        if self._contains_any(narrative, ["주소 오류", "주소 동기화", "주소가 잘못"]):
            platform_subcategories.append("address_sync_issue")

        categories: list[str] = []
        if merchant_subcategories:
            categories.append("merchant")
        if delivery_subcategories:
            categories.append("delivery_provider")
        if platform_subcategories:
            categories.append("platform")

        subcategories = sorted(set(merchant_subcategories + delivery_subcategories + platform_subcategories))
        if len(categories) == 0:
            primary_category = "needs_review"
            responsible_parties = ["internal_review"]
        elif len(categories) == 1:
            party = categories[0]
            responsible_parties = [party]
            primary_category = {
                "merchant": "merchant_issue",
                "delivery_provider": "delivery_issue",
                "platform": "platform_issue",
            }[party]
        else:
            primary_category = "multi_party_issue"
            responsible_parties = categories

        safety_flag = self._contains_any(
            narrative,
            ["이물", "머리카락", "벌레", "알레르기", "알러지", "상했", "덜 익", "위생", "식중독"],
        )
        if safety_flag:
            severity = "critical"
        elif self._contains_any(narrative, ["심각", "강한 불만", "너무 화", "최악", "심하게"]):
            severity = "high"
        elif self._contains_any(
            narrative,
            ["누락", "잘못된 메뉴", "지연", "오배송", "결제", "파손", "식어서"],
        ):
            severity = "medium"
        else:
            severity = "low"

        if self._contains_any(narrative, ["분노", "화가", "환불해", "최악", "짜증"]):
            customer_emotion = "angry"
        elif self._contains_any(narrative, ["불안", "무서", "위험", "병원", "아프"]):
            customer_emotion = "distressed"
        elif self._contains_any(narrative, ["불편", "문제", "실망", "속상"]):
            customer_emotion = "upset"
        else:
            customer_emotion = "calm"

        summary_fragment = "문제 원인이 아직 불명확해 추가 확인이 필요한 건"
        if primary_category == "merchant_issue":
            summary_fragment = "음식/조리 관련 이슈가 확인된 건"
        elif primary_category == "delivery_issue":
            summary_fragment = "배달 과정 이슈가 확인된 건"
        elif primary_category == "platform_issue":
            summary_fragment = "결제/주문 시스템 이슈가 확인된 건"
        elif primary_category == "multi_party_issue":
            summary_fragment = "여러 책임 주체가 동시에 관여한 복합 이슈로 보이는 건"

        return {
            "primary_category": primary_category,
            "subcategories": subcategories,
            "responsible_parties": responsible_parties,
            "severity": severity,
            "safety_flag": safety_flag,
            "customer_emotion": customer_emotion,
            "summary_fragment": summary_fragment,
        }

    def _resolve_requested_resolution(
        self,
        *,
        narrative: str,
        explicit_requests: list[str],
    ) -> list[str]:
        resolved: list[str] = []
        for request in explicit_requests:
            if request not in resolved:
                resolved.append(request)

        inferred = {
            "refund": ["환불", "취소", "결제 취소"],
            "redelivery": ["재배달", "다시 보내", "다시 배달"],
            "recook": ["재조리", "다시 만들어", "새로 조리"],
            "apology": ["사과", "죄송"],
            "investigation": ["확인", "조사", "검수"],
        }
        for key, keywords in inferred.items():
            if key in resolved:
                continue
            if self._contains_any(narrative, keywords):
                resolved.append(key)

        if not resolved:
            resolved.append("investigation")
        return resolved[:5]

    def _build_follow_up_questions(
        self,
        *,
        payload: IncidentAnalysisRequest,
        classification: dict[str, object],
        narrative: str,
    ) -> list[str]:
        questions: list[str] = []
        if not payload.order_id:
            questions.append("주문번호를 확인할 수 있을까요?")
        if classification["primary_category"] == "needs_review":
            questions.append("문제가 조리 단계에서 발생했는지, 배달 과정에서 발생했는지 구분 가능한 정보가 있을까요?")
        if payload.evidence_available == "unknown":
            questions.append("사진이나 영상 같은 증빙 자료가 있는지 확인 부탁드립니다.")
        if "late_delivery" in classification["subcategories"] and self._extract_delay_minutes(narrative) is None:
            questions.append("예정 시간보다 몇 분 정도 지연되었는지 기억나실까요?")
        return questions[:4]

    def _build_feedback_message(
        self,
        *,
        channel: str,
        send: bool,
        order_id: str | None,
        narrative: str,
        requested_resolution: list[str],
        safety_flag: bool,
    ) -> FeedbackMessage:
        if not send:
            return FeedbackMessage(send=False, message="")

        order_ref = order_id or "주문번호 미확인 건"
        request_text = ", ".join(requested_resolution)
        safety_text = "안전/위생 이슈 여부 확인이 필요합니다." if safety_flag else "안전 이슈는 현재 추가 확인 중입니다."

        if channel == "merchant":
            message = (
                f"[{order_ref}] 관련 고객 불만이 접수되었습니다. "
                f"고객은 '{narrative[:140]}'를 보고했고 요청 사항은 '{request_text}'입니다. {safety_text}"
            )
        elif channel == "delivery_provider":
            message = (
                f"[{order_ref}] 관련 배달 이슈가 접수되었습니다. "
                f"고객은 '{narrative[:140]}'를 보고했고 요청 사항은 '{request_text}'입니다."
            )
        else:
            message = (
                f"[{order_ref}] 관련 플랫폼 이슈가 접수되었습니다. "
                f"고객은 '{narrative[:140]}'를 보고했고 주문/결제/프로모션 반영 상태 확인이 필요합니다. "
                f"요청 사항은 '{request_text}'입니다."
            )

        return FeedbackMessage(send=True, message=message)

    def _build_internal_review_note(
        self,
        *,
        classification: dict[str, object],
        follow_up_questions: list[str],
    ) -> str:
        if classification["primary_category"] == "needs_review":
            return "책임 주체 확정 전 내부 검수 큐로 전달 필요."
        if follow_up_questions:
            return "추가 확인 질문 응답 수신 후 최종 라우팅 권장."
        return "분류 규칙에 따라 자동 라우팅 가능."

    def _extract_keyword_items(self, narrative: str, *, keyword: str) -> list[str]:
        if keyword not in narrative:
            return []
        return [f"{keyword} 관련 항목"]

    def _extract_delay_minutes(self, narrative: str) -> int | None:
        hour_match = re.search(r"(\\d+)\\s*시간", narrative)
        if hour_match:
            return int(hour_match.group(1)) * 60
        minute_match = re.search(r"(\\d+)\\s*분", narrative)
        if minute_match:
            return int(minute_match.group(1))
        return None

    def _contains_any(self, text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _responsible_party_label(self, parties: list[str]) -> str:
        labels = {
            "merchant": "음식점",
            "delivery_provider": "배달 서비스 업체",
            "platform": "플랫폼 운영팀",
            "internal_review": "내부 검수팀",
        }
        resolved = [labels.get(party, party) for party in parties]
        if not resolved:
            return "내부 검수팀"
        return "/".join(resolved)

    def _extract_items_from_lead(self, lead: dict[str, object] | None) -> list[str]:
        if not isinstance(lead, dict):
            return []
        incident_summary = str(lead.get("incident_summary") or "")
        marker = "주문메뉴:"
        if marker not in incident_summary:
            return []
        after = incident_summary.split(marker, 1)[1]
        before_next = after.split("/", 1)[0]
        return [item.strip() for item in before_next.split(",") if item.strip()]

    def _recording_object_key(self, *, lead_id: str, call_id: str, filename: str) -> str:
        extension = Path(filename).suffix or ".wav"
        return f"recordings/{lead_id}/{call_id}/{uuid4()}{extension}"

