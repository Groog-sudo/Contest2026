# 시스템 아키텍처 명세서

> 프로젝트: AI 활용 차세대 교육 솔루션 - AI 전화 멘토링 시스템  
> 버전: `0.3.0`  
> 최종 수정일: `2026-04-06`  
> 상태: STT/TTS/Storage/Queue 워커/대시보드 시계열 반영 완료

---

## 1. 아키텍처 목표

본 시스템은 다음의 폐쇄 루프를 구현하는 것을 목표로 합니다.

1. 상담 신청 접수
2. AI 멘토링 콜 요청
3. 통화 기록(STT) 저장
4. 상담 메모리 + 커리큘럼 기반 추천
5. TTS 기반 음성 안내 확장

---

## 2. 시스템 구성도

```text
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│      Lead Capture / Call Request / Knowledge Upload UI          │
└──────────────┬──────────────────────────────────┬───────────────┘
               │ REST API (JSON / multipart)      │
               ▼                                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                    API Layer (v1)                         │    │
│  │  /leads/register /calls/request                           │    │
│  │  /calls/recordings/upload /calls/transcripts/ingest       │    │
│  │  /calls/tts/preview /queue/tasks /queue/process           │    │
│  │  /queue/workers/run /dashboard/metrics                    │    │
│  │  /assessments/level-test /documents/upload                │    │
│  └──────────────────────────────┬────────────────────────────┘    │
│                                 ▼                                 │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │             Service Layer (MentoringService)             │    │
│  │  - 리드 등록                                             │    │
│  │  - 콜 스크립트 생성                                      │    │
│  │  - 전사 저장 및 요약                                     │    │
│  │  - 레벨 평가 및 추천                                     │    │
│  └──────────┬───────────────────────────┬───────────────────┘    │
│             ▼                           ▼                        │
│  ┌──────────────────────┐   ┌────────────────────────────────┐   │
│  │  SQLite Repository   │   │ External Clients               │   │
│  │  - leads             │   │ - STT client (mock/real)       │   │
│  │  - calls             │   │ - TTS client (mock/real)       │   │
│  │  - transcript turns  │   │ - OpenAI/Pinecone (planned)    │   │
│  │  - assessments       │   │ - Object storage (local/s3)    │   │
│  │  - knowledge_docs    │   │ - Call provider (planned)      │   │
│  │  - recordings/tasks  │   │                                │   │
│  └──────────────────────┘   └────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. 레이어 구조

| 계층 | 책임 | 주요 파일 |
| --- | --- | --- |
| Presentation | 상담 입력/요청 UI | `frontend/src/features/*` |
| API | 요청/응답 계약 및 라우팅 | `backend/app/api/v1/endpoints/*` |
| Service | 도메인 흐름 오케스트레이션 | `backend/app/services/mentoring_service.py` |
| Data | 영속 저장소 | `backend/app/db/repository.py` |
| External Client | STT/TTS/통신 연동 포인트 | `backend/app/clients/*.py` |
| Worker | 큐 작업 배치 실행 | `backend/app/workers/queue_worker.py` |

---

## 4. 핵심 컴포넌트

### 4.1 MentoringService

- 리드 등록 후 DB 저장
- 콜 스크립트 생성 및 상태 판정 (`drafted`, `script_ready`, `queued`)
- 전사 텍스트를 turn 단위로 저장하고 요약 생성
- 레벨 테스트 점수 정규화 후 추천 과정 생성
- TTS 프리뷰 URL 생성
- 녹취 업로드 -> 저장소 적재 -> `stt_transcription` 큐 등록
- 큐 재시도 정책 적용 (`QUEUE_MAX_ATTEMPTS`)

### 4.2 MentoringRepository (SQLite)

초기 실행 시 스키마를 자동 생성합니다.

- `leads`
- `calls`
- `call_transcript_turns`
- `assessments`
- `knowledge_documents`
- `recordings`
- `async_tasks`

### 4.3 STT/TTS Client

- STT:
  - provider `mock`: 고정 전사 텍스트 반환
  - provider `openai`: `OPENAI_STT_MODEL`로 전사
  - key 우선순위: `STT_PROVIDER_API_KEY` -> `OPENAI_API_KEY`
- TTS:
  - provider `mock`: 프리뷰 바이트 생성
  - provider `openai`: `OPENAI_TTS_MODEL`로 mp3 합성
  - key 우선순위: `TTS_PROVIDER_API_KEY` -> `OPENAI_API_KEY`
- 상세 구현 명세: `docs/media-pipeline-spec.md`

### 4.4 Object Storage Client

- provider `local`: 로컬 디렉터리에 파일 저장
- provider `s3`: `boto3` 기반 오브젝트 저장/조회
- 녹취 저장 키: `recordings/{lead_id}/{call_id}/{uuid}{ext}`
- TTS 프리뷰 키: `tts-previews/{uuid}.mp3`

### 4.5 Queue Worker

- `/queue/workers/run` 또는 업로드 후 BackgroundTask로 실행
- `queued` 상태 작업을 순차 처리
- 실패 시 재큐잉 또는 최종 실패로 전이

---

## 5. 데이터 흐름

### 5.1 리드 접수

`LeadCapturePanel -> POST /leads/register -> leads 저장`

### 5.2 콜 요청

`CallRequestPanel -> POST /calls/request -> calls 저장 -> 스크립트/근거 반환`

### 5.3 통화 전사 적재

`POST /calls/recordings/upload -> object storage 저장 -> async_tasks 큐 등록 -> worker 처리 -> call_transcript_turns 저장`

### 5.4 레벨 평가 및 추천

`POST /assessments/level-test -> 점수 정규화 -> 레벨 판정 -> assessments 저장`

### 5.5 TTS 프리뷰

`POST /calls/tts/preview -> TTS 합성 -> 저장소 적재 -> 음성 URL 메타데이터 반환`

---

## 6. 환경 변수 설계

| 그룹 | 변수 |
| --- | --- |
| DB | `APP_DB_PATH` |
| RAG | `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `PINECONE_NAMESPACE` |
| STT | `STT_PROVIDER_NAME`, `STT_PROVIDER_API_KEY`, `OPENAI_STT_MODEL` |
| TTS | `TTS_PROVIDER_NAME`, `TTS_PROVIDER_API_KEY`, `OPENAI_TTS_MODEL` |
| Storage | `OBJECT_STORAGE_PROVIDER`, `OBJECT_STORAGE_BUCKET`, `OBJECT_STORAGE_REGION`, `OBJECT_STORAGE_ENDPOINT_URL`, `OBJECT_STORAGE_ACCESS_KEY`, `OBJECT_STORAGE_SECRET_KEY`, `OBJECT_STORAGE_LOCAL_DIR`, `OBJECT_STORAGE_PUBLIC_BASE_URL` |
| Queue | `QUEUE_AUTO_PROCESS`, `QUEUE_MAX_ATTEMPTS` |
| Call | `CALL_PROVIDER_NAME`, `CALL_PROVIDER_API_KEY`, `OUTBOUND_CALL_FROM_NUMBER` |
| Common | `FRONTEND_ORIGIN` |

---

## 7. 현재 한계

- STT/TTS는 `openai`/`mock` 중심이며 기타 상용 프로바이더는 placeholder 수준
- 큐 워커는 API 기반 배치 실행이며 외부 스케줄러 상시 구동은 별도 구성 필요
- 추천 로직은 규칙 기반(점수 구간)이며 학습형 모델은 미적용
- 대화 히스토리 요약 고도화 및 검색 가중치 조정 미적용

---

## 8. 확장 계획

1. 외부 스케줄러와 큐 워커 연동 (Cron/APScheduler/Cloud Scheduler)
2. STT/TTS 다중 프로바이더 어댑터 추가
3. 상담 메모리 + 커리큘럼 하이브리드 RAG 검색 고도화
4. 추천 결과의 상담 전환율/학습 지속률 지표 고도화
