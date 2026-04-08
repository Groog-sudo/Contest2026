# Contest2026

AI 활용 차세대 교육 솔루션 공모전을 위한 연락처 기반 AI 전화 멘토링 프로젝트 모노레포입니다.

| 항목 | 내용 |
| --- | --- |
| 버전 | `0.3.0` |
| 최종 수정일 | `2026-04-08` |
| 현재 상태 | 리드 접수/콜 요청/녹취 업로드 큐/STT 전사 저장/TTS 프리뷰/레벨테스트/운영 대시보드 구현 + PostgreSQL/pgvector RAG 전환 + Unit/Smoke/Integration 테스트 검증 완료 |

## 1. 프로젝트 개요

본 프로젝트는 상담 신청부터 멘토링 추천까지의 흐름을 자동화하는 것을 목표로 합니다.

1. 수강생이 연락처와 상담 정보를 남긴다.
2. 운영자가 AI 멘토링 콜 요청을 생성한다.
3. 통화 전사(STT) 내용을 DB에 저장해 상담 메모리로 누적한다.
4. 수강생 수준 테스트 결과와 상담 메모리를 결합해 맞춤 과정을 추천한다.
5. 스크립트를 TTS로 미리 듣고 실제 통신 연동 단계로 확장한다.

## 2. 현재 구현 기능

### Backend API

- `GET /api/v1/health`
- `POST /api/v1/leads/register`
- `POST /api/v1/calls/request`
- `POST /api/v1/calls/recordings/upload`
- `POST /api/v1/calls/transcripts/ingest`
- `POST /api/v1/calls/tts/preview`
- `POST /api/v1/assessments/level-test`
- `GET /api/v1/dashboard/metrics`
- `GET /api/v1/queue/tasks`
- `POST /api/v1/queue/process`
- `POST /api/v1/queue/workers/run`
- `POST /api/v1/documents/upload`

### 데이터 저장

- 운영 권장 저장소: PostgreSQL + pgvector (`APP_DATABASE_URL`)
- 로컬 테스트 fallback: SQLite (`APP_DB_PATH`)
- 저장 테이블:
  - `leads`
  - `calls`
  - `call_transcript_turns`
  - `assessments`
  - `knowledge_documents`
  - `knowledge_document_chunks`
  - `recordings`
  - `async_tasks`

### AI/통신 확장 포인트

- STT 클라이언트 스텁: `backend/app/clients/stt_client.py`
- TTS 클라이언트 스텁: `backend/app/clients/tts_client.py`
- Object Storage 클라이언트: `backend/app/clients/storage_client.py`
- 통신사 발신 연동은 환경 변수 기반 구조만 반영 (실 호출은 후속 구현)
- 큐 처리 API: `backend/app/api/v1/endpoints/queue.py`
- 큐 워커 모듈: `backend/app/workers/queue_worker.py`
- 대시보드 집계 API: `backend/app/api/v1/endpoints/dashboard.py`

## 3. 디렉터리 구조

```text
Contest2026/
├── docs/
│   ├── architecture.md
│   ├── api-specification.md
│   ├── media-pipeline-spec.md
│   ├── testing-strategy.md
│   └── ai-report-outline.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   └── features/
│   │       ├── calls/
│   │       ├── knowledge/
│   │       └── leads/
│   └── .env.example
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── clients/
│   │   ├── db/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   └── .env.example
├── .env.example
└── README.md
```

## 4. 환경 변수

| 변수명 | 위치 | 설명 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Frontend | 백엔드 API 주소 |
| `APP_DATABASE_URL` | Backend | PostgreSQL 연결 문자열 (`pgvector` 확장 포함 권장) |
| `APP_DB_PATH` | Backend | SQLite 파일 경로 |
| `OPENAI_API_KEY` | Backend | 생성형 AI 연동 키 |
| `OPENAI_EMBEDDING_MODEL` | Backend | 임베딩 모델 |
| `OPENAI_EMBEDDING_DIMENSIONS` | Backend | pgvector 컬럼 차원 수 (기본 `1536`) |
| `OPENAI_STT_MODEL` | Backend | OpenAI STT 모델 |
| `OPENAI_TTS_MODEL` | Backend | OpenAI TTS 모델 |
| `OBJECT_STORAGE_PROVIDER` | Backend | 녹취 저장소 타입 (`local`/`s3`) |
| `OBJECT_STORAGE_BUCKET` | Backend | S3 버킷 이름 |
| `OBJECT_STORAGE_REGION` | Backend | S3 리전 |
| `OBJECT_STORAGE_ENDPOINT_URL` | Backend | S3 호환 엔드포인트 |
| `OBJECT_STORAGE_ACCESS_KEY` | Backend | 저장소 액세스 키 |
| `OBJECT_STORAGE_SECRET_KEY` | Backend | 저장소 시크릿 키 |
| `OBJECT_STORAGE_LOCAL_DIR` | Backend | 로컬 저장소 경로 |
| `OBJECT_STORAGE_PUBLIC_BASE_URL` | Backend | 공개 URL 베이스 |
| `STT_PROVIDER_NAME` | Backend | STT 프로바이더 식별자 |
| `STT_PROVIDER_API_KEY` | Backend | STT API 키 |
| `TTS_PROVIDER_NAME` | Backend | TTS 프로바이더 식별자 |
| `TTS_PROVIDER_API_KEY` | Backend | TTS API 키 |
| `QUEUE_AUTO_PROCESS` | Backend | 녹취 업로드 시 큐 자동 처리 여부 |
| `QUEUE_MAX_ATTEMPTS` | Backend | 큐 재시도 한도(실제 처리 로직 적용) |
| `CALL_PROVIDER_NAME` | Backend | 발신 프로바이더 식별자 |
| `CALL_PROVIDER_API_KEY` | Backend | 발신 API 키 |
| `OUTBOUND_CALL_FROM_NUMBER` | Backend | 발신 번호 |
| `FRONTEND_ORIGINS` | Backend | CORS 허용 오리진 목록(JSON 배열) |

### 4.1 런타임 `.env` 파일 위치

- Frontend 실행 시 `frontend/.env`를 읽습니다.
- Backend 실행 시 `backend/.env`를 읽습니다.
- 루트 `.env`는 공용 참조본으로 둘 수 있지만, 실제 실행값은 Frontend/Backend 각 디렉터리의 `.env`에 맞춰 두는 것을 권장합니다.
- `APP_DATABASE_URL`은 반드시 `vector` 확장이 활성화된 PostgreSQL 인스턴스를 가리켜야 합니다.

### 4.2 STT/TTS/녹취 파이프라인 요약 명세

| 항목 | 현재 구현 |
| --- | --- |
| STT provider | `mock`, `openai`, 기타 placeholder |
| TTS provider | `mock`, `openai`, 기타 placeholder |
| STT 키 우선순위 | `STT_PROVIDER_API_KEY` -> `OPENAI_API_KEY` |
| TTS 키 우선순위 | `TTS_PROVIDER_API_KEY` -> `OPENAI_API_KEY` |
| STT 모델 | `OPENAI_STT_MODEL` (기본 `gpt-4o-mini-transcribe`) |
| TTS 모델 | `OPENAI_TTS_MODEL` (기본 `gpt-4o-mini-tts`) |
| 녹취 저장 키 | `recordings/{lead_id}/{call_id}/{uuid}{ext}` |
| TTS 프리뷰 키 | `tts-previews/{uuid}.mp3` |
| 큐 작업 타입 | `stt_transcription` |
| 큐 재시도 | 실패 시 `attempts + 1 < QUEUE_MAX_ATTEMPTS`이면 재큐잉 |

파이프라인 흐름:

1. `POST /api/v1/calls/recordings/upload`로 녹취 업로드
2. Object Storage 저장 후 `recordings` 메타데이터 저장
3. `async_tasks`에 STT 작업(`queued`) 생성
4. 워커(`/api/v1/queue/workers/run` 또는 자동 처리) 실행
5. 전사 결과를 `call_transcript_turns`에 저장
6. 필요 시 `POST /api/v1/calls/tts/preview`로 스크립트 음성 프리뷰 생성

## 5. 실행 방법

### Frontend

```bash
cd frontend
npm install
# frontend/.env
# VITE_API_BASE_URL=http://localhost:8000
npm run dev
```

### Backend

```bash
docker compose -f docker-compose.pgvector.yml up -d

cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
# backend/.env
# APP_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/contest2026
# FRONTEND_ORIGINS=["http://localhost:5173"]
#
# 로컬 검증 프로필 예시(별도 pgvector 인스턴스):
# APP_DATABASE_URL=postgresql://postgres:<password>@127.0.0.1:5433/contest2026
uvicorn app.main:app --reload
```

## 6. 검증 상태

- Frontend: `npm run build` 통과
- Backend: `python -m pytest -q` 통과 (`19 passed`)
- Local PostgreSQL + pgvector: `contest2026` DB / `vector 0.8.1` 확장 / `127.0.0.1:5433` 연결 검증 완료

### 6.1 테스트 플로우 (권장)

1. Unit: `cd backend && python -m pytest -m unit -q`
2. Smoke: `cd backend && python -m pytest -m smoke -q` + `cd frontend && npm run build`
3. Integration: `cd backend && python -m pytest -m integration -q`

## 7. 문서 링크

- 아키텍처: [`docs/architecture.md`](docs/architecture.md)
- API 명세: [`docs/api-specification.md`](docs/api-specification.md)
- 음성 파이프라인 상세(STT/TTS/Storage/Queue): [`docs/media-pipeline-spec.md`](docs/media-pipeline-spec.md)
- 테스트 전략(Unit/Smoke/Integration): [`docs/testing-strategy.md`](docs/testing-strategy.md)
- AI 리포트 템플릿: [`docs/ai-report-outline.md`](docs/ai-report-outline.md)

## 8. 날짜별 작업 기록

| 날짜 | 담당 | 작업 내용 | 비고 |
| --- | --- | --- | --- |
| 2026-04-06 | AI | 프로젝트 초기 스캐폴드 구성 (Frontend/Backend/문서) | 기본 구조 |
| 2026-04-06 | AI | 리드 접수/콜 요청 중심으로 도메인 전환 | 교육 RAG 데모에서 상담 도메인으로 전환 |
| 2026-04-06 | AI | STT/TTS/상담기록 DB 연동 기반 백엔드 확장<br>`/api/v1/calls/transcripts/ingest`, `/api/v1/calls/tts/preview`, `/api/v1/assessments/level-test` 추가<br>SQLite Repository(`leads`, `calls`, `call_transcript_turns`, `assessments`, `knowledge_documents`) 반영 | `pytest -q` 10개 통과 |
| 2026-04-06 | AI | 문서/운영 워크플로우 동기화<br>`README.md`, `docs/architecture.md`, `docs/api-specification.md`, `docs/ai-report-outline.md`를 최신 설계로 갱신<br>`.agent/workflows/*`를 STT/TTS/DB/레벨평가 기준으로 업데이트 | `npm run build` 통과 |
| 2026-04-06 | AI | 운영 대시보드/큐 처리 흐름 추가<br>`/api/v1/dashboard/metrics`, `/api/v1/queue/tasks`, `/api/v1/queue/process`, `/api/v1/calls/recordings/upload` 반영<br>프론트 `MetricsPanel` 연결 및 큐 수동 처리 버튼 추가 | Backend `13 passed`, Frontend `build` 통과 |
| 2026-04-06 | AI | 큐 워커 분리/재시도 정책 및 기간 필터 시계열 대시보드 반영<br>`/api/v1/queue/workers/run`, `QUEUE_MAX_ATTEMPTS` 적용, `GET /api/v1/dashboard/metrics?period_days=7|14|30` 확장<br>프론트 대시보드에 기간 선택/시계열 막대 차트/워커 실행 버튼 추가 | Backend `14 passed`, Frontend `build` 통과 |
| 2026-04-06 | AI | STT/TTS/Storage/Queue 상세 명세 문서화<br>`docs/media-pipeline-spec.md` 신규 작성<br>`README.md`, `docs/architecture.md`, `docs/api-specification.md`에 상세 링크/요약 반영 | 코드 기준 동작 명세 고정 |
| 2026-04-06 | AI | 테스트 체계를 Unit/Smoke/Integration 플로우로 명세화<br>`docs/testing-strategy.md` 신규 작성, `backend/pytest.ini` 마커 정의(`unit`, `smoke`, `integration`) 반영<br>Unit 테스트(`test_unit_service_utils.py`) 추가 및 기존 테스트 분류 적용 | Backend `17 passed`, Frontend `build` 통과 |
| 2026-04-08 | AI | 운영 저장소를 PostgreSQL + pgvector 기준으로 전환<br>`APP_DATABASE_URL`/`OPENAI_EMBEDDING_DIMENSIONS` 추가, `MentoringRepository`를 PostgreSQL 우선 + SQLite fallback 구조로 확장<br>문서 청크를 `knowledge_document_chunks`에 저장하고 RAG 검색을 DB 내부 벡터 검색으로 교체 | Backend `19 passed` |
| 2026-04-08 | AI | 로컬 실행 환경을 PostgreSQL + pgvector 기준으로 검증하고 문서 업데이트<br>`backend/.env`, `frontend/.env` 런타임 위치를 README/architecture/testing 문서에 반영<br>로컬 검증 프로필(`127.0.0.1:5433`, `vector 0.8.1`)을 실행 가이드에 추가 | Frontend `build` 통과 |

## 9. 다음 단계 제안

1. 실 STT/TTS 프로바이더 SDK 연동
2. 큐 워커를 외부 스케줄러(Cron/APScheduler/Cloud Scheduler)와 연결해 상시 처리
3. 커리큘럼 문서 + 상담 메모리 하이브리드 RAG 검색 고도화
4. 대시보드 지표에 과정/상담원/유입채널 필터 및 CSV 내보내기 추가
