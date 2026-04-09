# Contest2026

> 버전: `0.5.0`  
> 마지막 수정일: `2026-04-09`  
> 상태: `PostgreSQL + ChromaDB 기반 배달 이슈 상담/분류 파이프라인 적용 완료`

## 1. 개요/목표

`ultimate_prompt_delivery_ai_consultant.md`를 기준으로 프로젝트 목적을 아래처럼 재정의했습니다.

1. 배달 주문 이후 고객 불만/이슈를 상담 형태로 접수
2. 이슈를 `merchant_issue`, `delivery_issue`, `platform_issue`, `multi_party_issue`, `needs_review`로 분류
3. 책임 주체를 판정하고 후속 전달 문안을 생성
4. 운영 시스템이 즉시 사용할 수 있는 구조화 JSON 생성
5. STT/TTS/RAG를 포함한 실제 운영 파이프라인 기반으로 확장 가능하게 구성

## 2. 현재 구현 범위

- 리드 접수: `POST /api/v1/leads/register`
- 상담 요청/스크립트: `POST /api/v1/calls/request`
- 녹음 업로드 + 큐 적재: `POST /api/v1/calls/recordings/upload`
- 전사 입력: `POST /api/v1/calls/transcripts/ingest`
- TTS 프리뷰: `POST /api/v1/calls/tts/preview`
- 이슈 분석(JSON): `POST /api/v1/analyses/analyze`
- 대시보드 지표: `GET /api/v1/dashboard/metrics`
- 큐 작업 조회/처리: `/api/v1/queue/*`
- 지식 문서 업로드(RAG): `POST /api/v1/documents/upload`

## 3. API/데이터 흐름

### 3.1 핵심 흐름

1. `leads/register`로 고객/주문/불만 요약 접수
2. `calls/request`로 상담 스크립트 생성
3. (선택) 녹음 업로드 시 `async_tasks`에 STT 작업 등록
4. 전사 텍스트 기반으로 `analyses/analyze` 호출
5. 분석 결과를 `incident_analyses`에 저장하고 대시보드 집계

### 3.2 저장소 구성

- PostgreSQL(정형 데이터)
  - `leads`, `calls`, `call_transcript_turns`, `incident_analyses`
  - `recordings`, `async_tasks`, `knowledge_documents`, `knowledge_document_chunks`
- ChromaDB(벡터 검색)
  - `CHROMA_COLLECTION_NAME` 컬렉션에 문서 임베딩 저장/검색

### 3.3 운영 DB 마이그레이션

- 구 스키마(PostgreSQL) -> 신규 스키마 이행 SQL 제공
  - `backend/sql/migrations/20260409_postgres_legacy_schema_to_delivery_issue.sql`
  - 가이드: `backend/sql/migrations/README.md`

## 4. 환경 변수

| 변수 | 설명 |
| --- | --- |
| `VITE_API_BASE_URL` | 프론트엔드 API Base URL |
| `APP_DATABASE_URL` | PostgreSQL 연결 문자열 |
| `APP_DB_PATH` | SQLite fallback 경로 |
| `OPENAI_API_KEY` | OpenAI API 키 |
| `OPENAI_EMBEDDING_MODEL` | 임베딩 모델 |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB 로컬 저장 경로 |
| `CHROMA_COLLECTION_NAME` | Chroma 컬렉션 이름 |
| `OPENAI_STT_MODEL` | STT 모델 |
| `OPENAI_TTS_MODEL` | TTS 모델 |
| `STT_PROVIDER_*` | STT provider 설정 |
| `TTS_PROVIDER_*` | TTS provider 설정 |
| `OBJECT_STORAGE_*` | 녹음/TTS 파일 저장소 설정 |
| `QUEUE_AUTO_PROCESS` | 업로드 시 자동 처리 여부 |
| `QUEUE_MAX_ATTEMPTS` | 큐 재시도 최대 횟수 |
| `FRONTEND_ORIGINS` | CORS 허용 origin 목록(JSON) |

## 5. 실행 방법

### 5.1 PostgreSQL

```bash
docker compose -f docker-compose.postgres.yml up -d
```

### 5.2 Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 5.3 Frontend

```bash
cd frontend
npm install
npm run dev
```

## 6. 테스트/검증 상태

- Backend: `python -m pytest -q` -> `19 passed`
- Frontend: `npm run build` -> 성공

검증 기준일: `2026-04-09`

## 7. 확장 계획

1. 분류 정확도 고도화(룰 + 모델 혼합)
2. 운영 DB 마이그레이션 자동화 파이프라인(배포 단계 통합)
3. 관제용 알림/라우팅(고위험 이슈 즉시 알림)
4. 문서 RAG 품질 개선(정책 문서 버전 관리)
