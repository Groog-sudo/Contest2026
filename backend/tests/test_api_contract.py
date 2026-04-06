from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_lead_registration_requires_consent() -> None:
    response = client.post(
        "/api/v1/leads/register",
        json={
            "student_name": "김수강",
            "phone_number": "010-1234-5678",
            "course_interest": "AI 취업 부트캠프",
            "learning_goal": "실무 프로젝트 경험을 쌓고 싶습니다.",
            "preferred_call_time": "평일 오후 7시 이후",
            "consent_to_call": False,
        },
    )

    assert response.status_code == 422


def test_lead_registration_returns_contract_shape() -> None:
    response = client.post(
        "/api/v1/leads/register",
        json={
            "student_name": "김수강",
            "phone_number": "010-1234-5678",
            "course_interest": "AI 취업 부트캠프",
            "learning_goal": "실무 프로젝트 경험을 쌓고 싶습니다.",
            "preferred_call_time": "평일 오후 7시 이후",
            "consent_to_call": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "captured"
    assert isinstance(payload["lead_id"], str)
    assert "상담 정보를 접수했습니다" in payload["next_action"]


def test_call_request_requires_non_empty_question() -> None:
    response = client.post(
        "/api/v1/calls/request",
        json={
            "lead_id": "lead-123",
            "student_name": "김수강",
            "phone_number": "010-1234-5678",
            "course_interest": "AI 취업 부트캠프",
            "student_question": "",
            "top_k": 3,
        },
    )

    assert response.status_code == 422


def test_call_request_returns_draft_when_unconfigured() -> None:
    response = client.post(
        "/api/v1/calls/request",
        json={
            "lead_id": "lead-123",
            "student_name": "김수강",
            "phone_number": "010-1234-5678",
            "course_interest": "AI 취업 부트캠프",
            "student_question": "어떤 커리큘럼으로 실무 포트폴리오를 만들 수 있나요?",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "drafted"
    assert isinstance(payload["call_id"], str)
    assert isinstance(payload["script_preview"], str)
    source_ids = [source["id"] for source in payload["sources"]]
    assert any(source_id == "intake-form" or source_id.startswith("call-memory-") for source_id in source_ids)


def test_transcript_ingest_returns_contract_shape() -> None:
    call_response = client.post(
        "/api/v1/calls/request",
        json={
            "lead_id": "lead-123",
            "student_name": "김수강",
            "phone_number": "010-1234-5678",
            "course_interest": "AI 취업 부트캠프",
            "student_question": "학습 순서를 추천해 주세요.",
            "top_k": 3,
        },
    )
    call_id = call_response.json()["call_id"]

    response = client.post(
        "/api/v1/calls/transcripts/ingest",
        json={
            "call_id": call_id,
            "lead_id": "lead-123",
            "transcript_text": (
                "student: 파이썬 기초가 약한데 어디부터 시작하면 좋을까요?\n"
                "ai: 기초 트랙부터 시작하고 주간 과제를 병행하는 방식을 추천드립니다."
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "stored"
    assert payload["saved_turns"] >= 2
    assert isinstance(payload["transcript_id"], str)
    assert "수강생 핵심 요청" in payload["summary"]


def test_tts_preview_returns_audio_metadata() -> None:
    response = client.post(
        "/api/v1/calls/tts/preview",
        json={
            "script": "안녕하세요. 상담 신청해 주셔서 감사합니다.",
            "voice": "mentor-ko",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "generated"
    assert payload["provider"] == "mock"
    assert payload["audio_url"]


def test_level_assessment_returns_recommended_course() -> None:
    response = client.post(
        "/api/v1/assessments/level-test",
        json={
            "lead_id": "lead-123",
            "answers": [
                {"area": "python", "score": 2},
                {"area": "data", "score": 3},
                {"area": "ai-concepts", "score": 2},
            ],
            "additional_context": "비전공자이며 주 10시간 학습 가능합니다.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["level"] in {"beginner", "intermediate", "advanced"}
    assert isinstance(payload["assessment_id"], str)
    assert isinstance(payload["recommended_course"], str)
    assert payload["score"] >= 0
    assert "curriculum-catalog" in payload["rag_context_ids"]


def test_recording_upload_enqueues_transcription_task() -> None:
    call_response = client.post(
        "/api/v1/calls/request",
        json={
            "lead_id": "lead-queue-1",
            "student_name": "김수강",
            "phone_number": "010-1234-5678",
            "course_interest": "AI 취업 부트캠프",
            "student_question": "통화 테스트",
            "top_k": 3,
        },
    )
    call_id = call_response.json()["call_id"]

    response = client.post(
        "/api/v1/calls/recordings/upload",
        data={"call_id": call_id, "lead_id": "lead-queue-1"},
        files={"file": ("recording.wav", b"fake-audio", "audio/wav")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "queued"
    assert isinstance(payload["queue_task_id"], str)
    assert payload["object_key"].startswith("recordings/")

    queue_response = client.get("/api/v1/queue/tasks")
    assert queue_response.status_code == 200
    queue_payload = queue_response.json()
    assert isinstance(queue_payload["items"], list)


def test_queue_process_returns_contract_shape() -> None:
    call_response = client.post(
        "/api/v1/calls/request",
        json={
            "lead_id": "lead-queue-2",
            "student_name": "김수강",
            "phone_number": "010-1234-5678",
            "course_interest": "AI 취업 부트캠프",
            "student_question": "큐 처리 테스트",
            "top_k": 3,
        },
    )
    call_id = call_response.json()["call_id"]

    upload_response = client.post(
        "/api/v1/calls/recordings/upload",
        data={"call_id": call_id, "lead_id": "lead-queue-2"},
        files={"file": ("recording.wav", b"fake-audio", "audio/wav")},
    )
    queue_task_id = upload_response.json()["queue_task_id"]

    process_response = client.post(
        "/api/v1/queue/process",
        json={"task_id": queue_task_id},
    )

    assert process_response.status_code == 200
    payload = process_response.json()
    assert payload["task_id"] == queue_task_id
    assert payload["status"] in {"done", "failed"}
    if payload["status"] == "done":
        assert isinstance(payload["result"], dict)
    else:
        assert isinstance(payload["error_message"], str)
    assert isinstance(payload["retry_queued"], bool)


def test_queue_worker_run_returns_contract_shape() -> None:
    response = client.post(
        "/api/v1/queue/workers/run",
        json={"limit": 5},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["requested_limit"] == 5
    assert isinstance(payload["processed"], int)
    assert isinstance(payload["succeeded"], int)
    assert isinstance(payload["requeued"], int)
    assert isinstance(payload["failed"], int)


def test_dashboard_metrics_returns_contract_shape() -> None:
    response = client.get("/api/v1/dashboard/metrics", params={"period_days": 14})

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["total_leads"], int)
    assert isinstance(payload["conversion_rate"], float)
    assert isinstance(payload["completion_rate"], float)
    assert "queued_tasks" in payload
    assert "failed_tasks" in payload
    assert payload["period_days"] == 14
    assert isinstance(payload["series"], list)
    assert len(payload["series"]) == 14
    first = payload["series"][0]
    assert isinstance(first["date"], str)
    assert isinstance(first["leads"], int)
    assert isinstance(first["calls"], int)
    assert isinstance(first["assessments"], int)


def test_document_upload_returns_contract_shape() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("sample.txt", b"hello contest", "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "knowledge_base_pending"
    assert isinstance(payload["document_id"], str)


def test_document_upload_requires_file() -> None:
    response = client.post("/api/v1/documents/upload")

    assert response.status_code == 422
