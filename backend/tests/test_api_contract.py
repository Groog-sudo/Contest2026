import pytest
from fastapi.testclient import TestClient

import os
import shutil
from pathlib import Path

TEST_DB_PATH = Path(__file__).parent / "test_api_contract.sqlite3"
TEST_CHROMA_PATH = Path(__file__).parent / ".chroma_test"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()
if TEST_CHROMA_PATH.exists():
    shutil.rmtree(TEST_CHROMA_PATH)

os.environ["APP_DATABASE_URL"] = ""
os.environ["APP_DB_PATH"] = str(TEST_DB_PATH)
os.environ["CHROMA_PERSIST_DIRECTORY"] = str(TEST_CHROMA_PATH)
os.environ["CHROMA_COLLECTION_NAME"] = "test_collection"
os.environ["OPENAI_API_KEY"] = ""

from app.main import app

client = TestClient(app)
pytestmark = pytest.mark.integration


def _build_lead_payload(consent: bool = True) -> dict[str, object]:
    return {
        "customer_name": "홍고객",
        "phone_number": "010-1234-5678",
        "order_id": "ORD-2026-0001",
        "order_items": ["치킨", "콜라"],
        "incident_summary": "배달이 1시간 이상 지연되고 음식이 식어서 도착했습니다.",
        "requested_resolution": "환불",
        "preferred_contact_time": "오늘 저녁",
        "consent_to_contact": consent,
    }


def _create_lead() -> str:
    response = client.post("/api/v1/leads/register", json=_build_lead_payload())
    assert response.status_code == 200
    return response.json()["lead_id"]


def _create_call(lead_id: str) -> str:
    response = client.post(
        "/api/v1/calls/request",
        json={
            "lead_id": lead_id,
            "customer_name": "홍고객",
            "phone_number": "010-1234-5678",
            "order_id": "ORD-2026-0001",
            "incident_summary": "배달이 늦고 음식 온도가 낮습니다.",
            "requested_resolution": "refund",
            "top_k": 3,
        },
    )
    assert response.status_code == 200
    return response.json()["call_id"]


def test_lead_registration_requires_consent() -> None:
    response = client.post("/api/v1/leads/register", json=_build_lead_payload(consent=False))
    assert response.status_code == 422


def test_lead_registration_returns_contract_shape() -> None:
    response = client.post("/api/v1/leads/register", json=_build_lead_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "captured"
    assert isinstance(payload["lead_id"], str)
    assert "배달 불만 접수" in payload["next_action"]


def test_call_request_requires_non_empty_summary() -> None:
    lead_id = _create_lead()
    response = client.post(
        "/api/v1/calls/request",
        json={
            "lead_id": lead_id,
            "customer_name": "홍고객",
            "phone_number": "010-1234-5678",
            "order_id": "ORD-2026-0001",
            "incident_summary": "",
            "requested_resolution": "refund",
            "top_k": 3,
        },
    )

    assert response.status_code == 422


def test_call_request_returns_draft_when_unconfigured() -> None:
    lead_id = _create_lead()
    response = client.post(
        "/api/v1/calls/request",
        json={
            "lead_id": lead_id,
            "customer_name": "홍고객",
            "phone_number": "010-1234-5678",
            "order_id": "ORD-2026-0001",
            "incident_summary": "배달 지연 및 음식 상태 이상",
            "requested_resolution": "refund",
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
    lead_id = _create_lead()
    call_id = _create_call(lead_id)

    response = client.post(
        "/api/v1/calls/transcripts/ingest",
        json={
            "call_id": call_id,
            "lead_id": lead_id,
            "transcript_text": (
                "customer: 주문이 늦게 도착했고 음식이 차갑습니다.\n"
                "ai: 불편을 드려 죄송합니다. 지연 시간을 확인하겠습니다."
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "stored"
    assert payload["saved_turns"] >= 2
    assert isinstance(payload["transcript_id"], str)
    assert "고객 핵심 이슈" in payload["summary"]


def test_tts_preview_returns_audio_metadata() -> None:
    response = client.post(
        "/api/v1/calls/tts/preview",
        json={
            "script": "불편을 겪으셔서 죄송합니다. 주문번호부터 확인하겠습니다.",
            "voice": "agent-ko",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "generated"
    assert payload["provider"] == "mock"
    assert payload["audio_url"]


def test_incident_analysis_returns_structured_json() -> None:
    lead_id = _create_lead()
    call_id = _create_call(lead_id)

    response = client.post(
        "/api/v1/analyses/analyze",
        json={
            "lead_id": lead_id,
            "call_id": call_id,
            "customer_message": "배달이 70분 늦었고 음식이 식었어요. 환불 원합니다.",
            "order_id": "ORD-2026-0001",
            "order_items": ["치킨", "콜라"],
            "evidence_available": "photo",
            "requested_resolution": ["refund"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["primary_category"] in {
        "merchant_issue",
        "delivery_issue",
        "platform_issue",
        "multi_party_issue",
        "needs_review",
    }
    assert payload["severity"] in {"low", "medium", "high", "critical"}
    assert isinstance(payload["subcategories"], list)
    assert isinstance(payload["responsible_parties"], list)
    assert isinstance(payload["merchant_feedback"]["send"], bool)
    assert isinstance(payload["issue_details"]["reported_problem"], str)


def test_recording_upload_enqueues_transcription_task() -> None:
    lead_id = _create_lead()
    call_id = _create_call(lead_id)

    response = client.post(
        "/api/v1/calls/recordings/upload",
        data={"call_id": call_id, "lead_id": lead_id},
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
    lead_id = _create_lead()
    call_id = _create_call(lead_id)

    upload_response = client.post(
        "/api/v1/calls/recordings/upload",
        data={"call_id": call_id, "lead_id": lead_id},
        files={"file": ("recording.wav", b"fake-audio", "audio/wav")},
    )
    queue_task_id = upload_response.json()["queue_task_id"]

    process_response = client.post("/api/v1/queue/process", json={"task_id": queue_task_id})

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
    response = client.post("/api/v1/queue/workers/run", json={"limit": 5})

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
    assert isinstance(payload["resolution_rate"], float)
    assert isinstance(payload["high_risk_cases"], int)
    assert "queued_tasks" in payload
    assert "failed_tasks" in payload
    assert payload["period_days"] == 14
    assert isinstance(payload["series"], list)
    assert len(payload["series"]) == 14
    first = payload["series"][0]
    assert isinstance(first["date"], str)
    assert isinstance(first["leads"], int)
    assert isinstance(first["calls"], int)
    assert isinstance(first["analyses"], int)
    assert isinstance(first["high_risk"], int)


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
