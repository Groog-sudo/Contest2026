import pytest

from app.core.config import Settings
from app.services.mentoring_service import MentoringService

pytestmark = pytest.mark.unit


def build_service(tmp_path) -> MentoringService:
    settings = Settings(
        APP_DB_PATH=str(tmp_path / "unit-test.sqlite3"),
        STT_PROVIDER_NAME="mock",
        TTS_PROVIDER_NAME="mock",
    )
    return MentoringService(settings)


def test_score_to_level_boundaries(tmp_path) -> None:
    service = build_service(tmp_path)

    assert service._score_to_level(0) == "beginner"
    assert service._score_to_level(39) == "beginner"
    assert service._score_to_level(40) == "intermediate"
    assert service._score_to_level(69) == "intermediate"
    assert service._score_to_level(70) == "advanced"
    assert service._score_to_level(100) == "advanced"


def test_parse_transcript_text_normalizes_speakers(tmp_path) -> None:
    service = build_service(tmp_path)

    turns = service._parse_transcript_text(
        "student: 안녕하세요\nmentor: 커리큘럼 안내\nai: 좋아요\n그냥 문장"
    )

    assert turns[0]["speaker"] == "student"
    assert turns[1]["speaker"] == "student"
    assert turns[1]["utterance"] == "커리큘럼 안내"
    assert turns[2]["speaker"] == "ai"
    assert turns[3]["speaker"] == "student"


def test_summarize_turns_uses_student_and_ai_lines(tmp_path) -> None:
    service = build_service(tmp_path)

    summary = service._summarize_turns(
        [
            {"speaker": "student", "utterance": "기초부터 배우고 싶어요."},
            {"speaker": "ai", "utterance": "기초 트랙부터 시작합시다."},
        ]
    )

    assert "기초부터 배우고 싶어요." in summary
    assert "기초 트랙부터 시작합시다." in summary
