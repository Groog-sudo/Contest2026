---
description: README 및 docs 문서를 최신 구현 상태에 맞춰 갱신하는 절차
---

# 문서 갱신 절차

현재 프로젝트 문서는 아래 4개를 같은 양식으로 유지합니다.

- `README.md`
- `docs/architecture.md`
- `docs/api-specification.md`
- `docs/ai-report-outline.md`

## 1. 공통 양식

문서 업데이트 시 아래 순서를 기본으로 유지합니다.

1. 메타 정보 (버전, 수정일, 상태)
2. 개요/목표
3. 현재 구현 범위
4. API/데이터 흐름
5. 환경 변수
6. 테스트/검증 상태
7. 확장 계획

## 2. 문서별 업데이트 기준

| 문서 | 갱신 조건 |
| --- | --- |
| `README.md` | 기능 추가/삭제, 환경 변수 변경, 실행 절차 변경 |
| `docs/architecture.md` | 모듈 구조, 데이터 흐름, 저장소/외부 연동 구조 변경 |
| `docs/api-specification.md` | 엔드포인트, 요청/응답 스키마, 검증 규칙 변경 |
| `docs/ai-report-outline.md` | 제출 서사/구성 항목 업데이트 필요 시 |

## 3. 현재 필수 반영 항목

문서를 갱신할 때 아래 내용 누락 여부를 반드시 확인합니다.

- STT 전사 적재 API: `/api/v1/calls/transcripts/ingest`
- TTS 프리뷰 API: `/api/v1/calls/tts/preview`
- 레벨 테스트 API: `/api/v1/assessments/level-test`
- DB 경로 변수: `APP_DB_PATH`
- STT/TTS 변수: `STT_*`, `TTS_*`
- 계약 테스트 파일: `backend/tests/test_api_contract.py`

## 4. 갱신 후 검증

// turbo
```bash
cd backend && .venv\Scripts\python -m pytest -q
```

// turbo
```bash
cd frontend && npm run build
```

문서와 실제 구현이 어긋나지 않는 상태를 유지합니다.
