from __future__ import annotations

from uuid import uuid4

from fastapi import UploadFile

from app.clients.stt_client import STTClient
from app.clients.tts_client import TTSClient
from app.core.config import Settings
from app.db.repository import MentoringRepository
from app.schemas.assessment import LevelAssessmentRequest, LevelAssessmentResponse
from app.schemas.call import (
    CallRequest,
    CallRequestResponse,
    CallSourceItem,
    CallTranscriptIngestRequest,
    CallTranscriptIngestResponse,
    TTSPreviewRequest,
    TTSPreviewResponse,
)
from app.schemas.lead import LeadRegistrationRequest, LeadRegistrationResponse


class MentoringService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repository = MentoringRepository(settings.app_db_path)
        self.stt_client = STTClient(settings)
        self.tts_client = TTSClient(settings)

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
            next_step = (
                "RAG 기반 멘토링 스크립트를 사용해 아웃바운드 콜 큐에 등록합니다."
            )
        elif self.settings.rag_configured:
            status = "script_ready"
            next_step = (
                "멘토링 스크립트는 준비되었습니다. 통신 연동 후 자동 발신을 연결하세요."
            )
        else:
            status = "drafted"
            next_step = (
                "현재는 지식베이스와 통신 연동이 없어 초안 스크립트만 생성했습니다."
            )

        script_preview = self._build_script_preview(payload, status=status, lead=lead)
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
            sources=self._build_sources(lead_id=payload.lead_id, course_interest=payload.course_interest),
            next_step=next_step,
        )

    async def ingest(self, file: UploadFile) -> dict[str, str]:
        document_id = str(uuid4())
        await file.read()
        await file.close()

        status = "accepted" if self.settings.rag_configured else "knowledge_base_pending"
        self.repository.save_document(
            document_id=document_id,
            filename=file.filename or "unknown",
            status=status,
        )
        return {"document_id": document_id, "status": status}

    def ingest_call_transcript(
        self,
        payload: CallTranscriptIngestRequest,
    ) -> CallTranscriptIngestResponse:
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

    def create_tts_preview(self, payload: TTSPreviewRequest) -> TTSPreviewResponse:
        audio_url, mime_type = self.tts_client.synthesize(
            script=payload.script,
            voice=payload.voice,
        )
        return TTSPreviewResponse(
            status="generated",
            provider=self.tts_client.provider_name,
            voice=payload.voice,
            audio_url=audio_url,
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

    def _build_script_preview(
        self,
        payload: CallRequest,
        *,
        status: str,
        lead: dict[str, str] | None,
    ) -> str:
        learning_goal = lead["learning_goal"] if lead else "학습 목표를 재확인합니다."
        opening = (
            f"안녕하세요, {payload.student_name} 님. 남겨주신 {payload.course_interest} 문의를 보고 "
            "AI 멘토가 전화드렸습니다."
        )
        need = (
            f"현재 가장 궁금하신 부분은 '{payload.student_question}'로 이해했습니다. "
            "먼저 목표와 학습 배경을 짧게 확인한 뒤 맞춤형 안내를 드리겠습니다."
        )
        guidance = (
            f"기존 목표는 '{learning_goal}'로 파악되어 있으며, 학습 수준 테스트 후 과정을 연결합니다."
        )
        closing = {
            "queued": "통화가 끝나면 상담 요약과 다음 액션을 문자 또는 CRM에 기록합니다.",
            "script_ready": "운영자가 이 스크립트를 검토한 뒤 수동 상담에 활용할 수 있습니다.",
            "drafted": "현재는 업로드된 RAG 자료가 없어 일반 상담 흐름 기준 초안을 제공합니다.",
        }[status]
        return " ".join([opening, need, guidance, closing])

    def _build_sources(self, *, lead_id: str, course_interest: str) -> list[CallSourceItem]:
        sources: list[CallSourceItem] = []

        recent_utterances = self.repository.list_recent_utterances(lead_id=lead_id, limit=2)
        for index, memory in enumerate(recent_utterances, start=1):
            text = memory["utterance"][:40]
            sources.append(
                CallSourceItem(
                    id=f"call-memory-{index}",
                    title=f"상담 이력 메모리: {text}",
                    score=0.7,
                )
            )

        if self.settings.rag_configured:
            sources.extend(
                [
                    CallSourceItem(
                        id="mentor-playbook",
                        title=f"{course_interest} 상담 플레이북",
                        score=0.91,
                    ),
                    CallSourceItem(
                        id="faq-snippets",
                        title=f"{course_interest} 자주 묻는 질문 요약",
                        score=0.84,
                    ),
                ]
            )

        if not sources:
            sources.append(
                CallSourceItem(
                    id="intake-form",
                    title="수강생 상담 신청서 기반 초안",
                    score=None,
                )
            )

        return sources

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
