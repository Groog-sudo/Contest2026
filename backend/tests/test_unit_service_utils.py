import pytest

from app.core.config import Settings
from app.services.delivery_issue_service import DeliveryIssueService

pytestmark = pytest.mark.unit


def build_service(tmp_path) -> DeliveryIssueService:
    settings = Settings(
        APP_DATABASE_URL="",
        APP_DB_PATH=str(tmp_path / "unit-test.sqlite3"),
        STT_PROVIDER_NAME="mock",
        TTS_PROVIDER_NAME="mock",
    )
    return DeliveryIssueService(settings)


def test_parse_transcript_text_normalizes_speakers(tmp_path) -> None:
    service = build_service(tmp_path)

    turns = service._parse_transcript_text(
        "student: hello\nmentor: let me confirm your order id\nai: understood\njust a sentence"
    )

    assert turns[0]["speaker"] == "customer"
    assert turns[1]["speaker"] == "ai"
    assert turns[2]["speaker"] == "ai"
    assert turns[3]["speaker"] == "customer"


def test_summarize_turns_uses_customer_and_ai_lines(tmp_path) -> None:
    service = build_service(tmp_path)

    summary = service._summarize_turns(
        [
            {"speaker": "customer", "utterance": "delivery was late"},
            {"speaker": "ai", "utterance": "I will verify the timeline"},
        ]
    )

    assert "delivery was late" in summary
    assert "I will verify the timeline" in summary


def test_classify_issue_flags_critical_safety(tmp_path) -> None:
    service = build_service(tmp_path)

    result = service._classify_issue(
        "\uc74c\uc2dd\uc5d0 \uba38\ub9ac\uce74\ub77d\uc774 \ub4e4\uc5b4\uc788\uc5b4\uc11c \uc704\uc0dd \uc774\uc288\ub85c \ubcf4\uace0\ud569\ub2c8\ub2e4"
    )

    assert result["primary_category"] == "merchant_issue"
    assert result["safety_flag"] is True
    assert result["severity"] == "critical"


def test_sqlite_fallback_disables_vector_search(tmp_path) -> None:
    service = build_service(tmp_path)

    assert service.settings.database_backend == "sqlite"
    assert service.repository.supports_vector_search == service.settings.chroma_enabled
    assert service.settings.rag_configured is False


def test_postgres_settings_enable_rag_when_openai_key_present() -> None:
    settings = Settings(
        APP_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/contest2026",
        OPENAI_API_KEY="test-key",
        CHROMA_PERSIST_DIRECTORY="./data/chroma-test",
        CHROMA_COLLECTION_NAME="test-collection",
        STT_PROVIDER_NAME="mock",
        TTS_PROVIDER_NAME="mock",
    )

    assert settings.database_backend == "postgresql"
    assert settings.chroma_enabled is True
    assert settings.rag_configured is True
