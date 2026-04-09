# API Specification

> Base URL: `http://localhost:8000/api/v1`  
> 버전: `0.5.0`  
> 마지막 수정일: `2026-04-09`

## 1. 개요/목표

배달 이슈 상담 도메인에서 사용하는 API 계약을 정의합니다.

## 2. 현재 구현 범위

| Method | Endpoint | 설명 |
| --- | --- | --- |
| GET | `/health` | 헬스체크 |
| POST | `/leads/register` | 고객 불만 리드 접수 |
| POST | `/calls/request` | 상담 스크립트 요청 |
| POST | `/calls/transcripts/ingest` | 전사 텍스트 저장 |
| POST | `/calls/recordings/upload` | 녹음 업로드 + 큐 등록 |
| POST | `/calls/tts/preview` | TTS 프리뷰 생성 |
| POST | `/analyses/analyze` | 이슈 분석(JSON) 생성 |
| GET | `/dashboard/metrics` | 운영 지표 조회 |
| GET | `/queue/tasks` | 큐 작업 목록 |
| POST | `/queue/process` | 큐 단건 처리 |
| POST | `/queue/workers/run` | 큐 배치 처리 |
| POST | `/documents/upload` | 지식 문서 업로드 |

## 3. 요청/응답 핵심 계약

### 3.1 `POST /leads/register`

요청 필드(핵심):
- `customer_name`, `phone_number`, `order_id`
- `incident_summary`, `consent_to_contact`

응답 필드:
- `lead_id`, `status`, `next_action`

### 3.2 `POST /calls/request`

요청 필드(핵심):
- `lead_id`, `customer_name`, `phone_number`
- `incident_summary`, `top_k`

응답 필드:
- `call_id`, `status`, `script_preview`, `sources`, `next_step`

### 3.3 `POST /analyses/analyze`

요청 필드(핵심):
- `lead_id`, `call_id`
- `customer_message` or `transcript_text`
- `order_id`, `order_items`, `requested_resolution`

응답 필드(핵심):
- `primary_category`, `subcategories`, `responsible_parties`
- `severity`, `safety_flag`, `customer_emotion`
- `merchant_feedback`, `delivery_feedback`, `platform_feedback`
- `summary_for_customer`, `internal_review_note`

### 3.4 `GET /dashboard/metrics`

쿼리:
- `period_days` (`7~90`)

응답 필드(핵심):
- `total_leads`, `leads_with_calls`, `leads_with_analyses`
- `conversion_rate`, `resolution_rate`, `high_risk_cases`
- `series[]`: `date`, `leads`, `calls`, `analyses`, `high_risk`

## 4. 데이터/운영 참고

- 분석 데이터 저장 테이블: `incident_analyses`
- 전사 비동기 처리: `async_tasks`
- 문서 RAG 저장: `knowledge_documents`, `knowledge_document_chunks`, ChromaDB

## 5. 환경 변수

- `APP_DATABASE_URL`, `APP_DB_PATH`
- `CHROMA_PERSIST_DIRECTORY`, `CHROMA_COLLECTION_NAME`
- `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_STT_MODEL`, `OPENAI_TTS_MODEL`
- `STT_PROVIDER_*`, `TTS_PROVIDER_*`, `OBJECT_STORAGE_*`
- `QUEUE_AUTO_PROCESS`, `QUEUE_MAX_ATTEMPTS`

## 6. 테스트/검증 상태

- API 계약 검증 테스트: `backend/tests/test_api_contract.py`
- 검증 결과: `19 passed`

## 7. 확장 계획

1. 응답 스키마 버전 필드 도입(`schema_version`)
2. 분석 Explainability 필드 확대
3. 외부 티켓 시스템 API 계약 추가
