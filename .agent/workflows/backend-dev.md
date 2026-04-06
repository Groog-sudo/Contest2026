---
description: 백엔드 개발 서버 실행, 환경 변수 설정, 계약 테스트 검증
---

# 백엔드 실행 가이드

## 1. 가상 환경 및 의존성 설치

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
```

// turbo
```bash
cd backend && .venv\Scripts\pip install -r requirements.txt
```

## 2. 개발 서버 실행

// turbo
```bash
cd backend && .venv\Scripts\python -m uvicorn app.main:app --reload
```

- 기본 주소: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

## 3. 환경 변수 설정

```bash
cd backend && copy .env.example .env
```

### 핵심 환경 변수

| 변수명 | 설명 |
| --- | --- |
| `APP_DB_PATH` | SQLite 파일 경로 |
| `OPENAI_API_KEY` | 생성형 AI 연동 키 |
| `PINECONE_API_KEY` | Pinecone 연동 키 |
| `PINECONE_INDEX_NAME` | Pinecone 인덱스 이름 |
| `PINECONE_NAMESPACE` | Pinecone namespace |
| `STT_PROVIDER_NAME` | STT 프로바이더 이름 (기본 `mock`) |
| `STT_PROVIDER_API_KEY` | STT API 키 |
| `TTS_PROVIDER_NAME` | TTS 프로바이더 이름 (기본 `mock`) |
| `TTS_PROVIDER_API_KEY` | TTS API 키 |
| `CALL_PROVIDER_NAME` | 통신 프로바이더 이름 |
| `CALL_PROVIDER_API_KEY` | 통신 API 키 |
| `OUTBOUND_CALL_FROM_NUMBER` | 발신 번호 |

## 4. 현재 API 범위

- `GET /api/v1/health`
- `POST /api/v1/leads/register`
- `POST /api/v1/calls/request`
- `POST /api/v1/calls/transcripts/ingest`
- `POST /api/v1/calls/tts/preview`
- `POST /api/v1/assessments/level-test`
- `POST /api/v1/documents/upload`

## 5. 테스트 실행

// turbo
```bash
cd backend && .venv\Scripts\python -m pytest -q
```

- 계약 테스트 파일: `backend/tests/test_api_contract.py`
- 헬스체크 테스트 파일: `backend/tests/test_health.py`

## 6. 구현 원칙

- 엔드포인트: `backend/app/api/v1/endpoints/`
- 스키마: `backend/app/schemas/`
- 서비스 로직: `backend/app/services/`
- 저장소/DB: `backend/app/db/`
- 외부 연동(STT/TTS/Pinecone 등): `backend/app/clients/`

신규 기능은 엔드포인트에 직접 로직을 넣지 말고 서비스/저장소로 분리합니다.
