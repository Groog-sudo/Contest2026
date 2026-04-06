from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_query_requires_non_empty_question() -> None:
    response = client.post("/api/v1/chat/query", json={"question": "", "top_k": 3})

    assert response.status_code == 422


def test_chat_query_returns_guidance_when_unconfigured() -> None:
    response = client.post(
        "/api/v1/chat/query",
        json={"question": "이번 주 과제 제출 규칙을 알려줘", "top_k": 3},
    )

    assert response.status_code == 503
    assert "RAG service is not configured yet" in response.json()["detail"]


def test_document_upload_returns_contract_shape() -> None:
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("sample.txt", b"hello contest", "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "unconfigured"
    assert isinstance(payload["document_id"], str)


def test_document_upload_requires_file() -> None:
    response = client.post("/api/v1/documents/upload")

    assert response.status_code == 422
