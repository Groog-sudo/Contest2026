# API 명세서

> 프로젝트: AI 활용 차세대 교육 솔루션 - AI 전화 멘토링 시스템  
> API 버전: `v1`  
> Base URL: `http://localhost:8000/api/v1`  
> 최종 수정일: `2026-04-08`  
> 상태: 구현 반영 완료 (스캐폴드 + PostgreSQL/pgvector RAG + DB 저장 + 큐 워커/재시도 + 기간 시계열 대시보드)
> 음성 처리 상세 문서: `docs/media-pipeline-spec.md`
> 테스트 플로우 상세 문서: `docs/testing-strategy.md`

---

## 1. 공통 규칙

| 항목 | 값 |
| --- | --- |
| 프로토콜 | HTTP (개발), HTTPS (운영 예정) |
| 인코딩 | UTF-8 |
| Content-Type | `application/json`, `multipart/form-data` |
| 인증 | 현재 없음 |

### 1.1 공통 에러 형식

```json
{
  "detail": "에러 메시지"
}
```

### 1.2 주요 상태 코드

| 코드 | 설명 |
| --- | --- |
| `200` | 요청 성공 |
| `422` | 요청 검증 실패 |

---

## 2. 엔드포인트 목록

| Method | Endpoint | 설명 |
| --- | --- | --- |
| `GET` | `/health` | 서버 상태 확인 |
| `POST` | `/leads/register` | 상담 신청 리드 접수 |
| `POST` | `/calls/request` | AI 멘토링 콜 요청 |
| `POST` | `/calls/recordings/upload` | 녹취 파일 업로드 및 전사 큐 등록 |
| `POST` | `/calls/transcripts/ingest` | 통화 전사(STT) 저장 |
| `POST` | `/calls/tts/preview` | 멘토링 스크립트 TTS 프리뷰 |
| `POST` | `/assessments/level-test` | 레벨 평가 및 과정 추천 |
| `GET` | `/dashboard/metrics` | 상담 성과 집계 지표 조회 |
| `GET` | `/queue/tasks` | 비동기 작업 큐 목록 조회 |
| `POST` | `/queue/process` | 단일 큐 작업 수동 처리 |
| `POST` | `/queue/workers/run` | 큐 워커 배치 실행 |
| `POST` | `/documents/upload` | 지식 문서 업로드 |

---

## 3. 엔드포인트 상세

### 3.1 `GET /health`

응답 예시:

```json
{
  "status": "ok"
}
```

---

### 3.2 `POST /leads/register`

설명: 수강생 상담 신청을 접수하고 `lead_id`를 생성합니다.

요청 예시:

```json
{
  "student_name": "김수강",
  "phone_number": "010-1234-5678",
  "course_interest": "AI 취업 부트캠프",
  "learning_goal": "실무 프로젝트 경험을 쌓고 싶습니다.",
  "preferred_call_time": "평일 오후 7시 이후",
  "consent_to_call": true
}
```

응답 예시:

```json
{
  "lead_id": "f7dbff7a-2cb7-4be5-a684-2f1bfd55f7c1",
  "status": "captured",
  "next_action": "김수강 님 상담 정보를 접수했습니다. 이제 AI 멘토링 콜 요청을 생성해 연락 흐름을 이어갈 수 있습니다."
}
```

검증 규칙:

- `phone_number`: 숫자 기준 8자리 이상
- `consent_to_call`: 반드시 `true`

---

### 3.3 `POST /calls/request`

설명: 리드 정보를 바탕으로 멘토링 콜 스크립트를 생성하고 상태를 반환합니다.

요청 예시:

```json
{
  "lead_id": "lead-123",
  "student_name": "김수강",
  "phone_number": "010-1234-5678",
  "course_interest": "AI 취업 부트캠프",
  "student_question": "비전공자는 어떤 순서로 준비하면 좋을까요?",
  "top_k": 3
}
```

응답 예시:

```json
{
  "call_id": "29be2ab0-4b38-473f-a841-7604d6fd4018",
  "status": "drafted",
  "script_preview": "안녕하세요, 김수강 님...",
  "sources": [
    {
      "id": "intake-form",
      "title": "수강생 상담 신청서 기반 초안",
      "score": null
    }
  ],
  "next_step": "현재는 지식베이스와 통신 연동이 없어 초안 스크립트만 생성했습니다."
}
```

`status` 값:

| 값 | 의미 |
| --- | --- |
| `drafted` | 기본 스크립트 초안 생성 |
| `script_ready` | RAG 근거 반영 완료 (자동 발신 미연동) |
| `queued` | 자동 발신 큐 등록 가능 상태 |

---

### 3.4 `POST /calls/recordings/upload`

설명: 녹취 파일을 업로드하고 STT 전사 작업을 큐(`async_tasks`)에 등록합니다.

요청:

- `multipart/form-data`
- 필드: `file`, `call_id`, `lead_id`

응답 예시:

```json
{
  "recording_id": "02f2ef36-5fbe-4c97-bf80-f99ce9707fbb",
  "status": "queued",
  "object_key": "recordings/lead-queue-1/29be2ab0.../d623...wav",
  "storage_url": "local://recordings/lead-queue-1/29be2ab0.../d623...wav",
  "queue_task_id": "6e2cc339-0b1c-4f50-bf34-cf19a02247a0"
}
```

참고:

- `QUEUE_AUTO_PROCESS=true`인 경우 업로드 직후 백그라운드에서 큐 처리가 시작됩니다.

---

### 3.5 `POST /calls/transcripts/ingest`

설명: 통화 전사 내용을 저장합니다. 아래 중 최소 하나가 필요합니다.

- `turns`
- `transcript_text`
- `recording_url` (STT 연동 지점)

요청 예시:

```json
{
  "call_id": "29be2ab0-4b38-473f-a841-7604d6fd4018",
  "lead_id": "lead-123",
  "transcript_text": "student: 파이썬 기초가 약합니다.\nai: 기초 트랙부터 시작해요."
}
```

응답 예시:

```json
{
  "transcript_id": "a3cbce5a-8e13-4f95-9af8-89ec2ea61d9d",
  "status": "stored",
  "saved_turns": 2,
  "summary": "수강생 핵심 요청: 파이썬 기초가 약합니다. / 상담 가이드: 기초 트랙부터 시작해요."
}
```

---

### 3.6 `POST /calls/tts/preview`

설명: 스크립트를 TTS로 변환한 결과 메타데이터를 반환합니다.

요청 예시:

```json
{
  "script": "안녕하세요. 상담 신청해 주셔서 감사합니다.",
  "voice": "mentor-ko"
}
```

응답 예시:

```json
{
  "status": "generated",
  "provider": "mock",
  "voice": "mentor-ko",
  "audio_url": "https://mock-tts.local/preview?voice=mentor-ko&q=...",
  "mime_type": "mock/mp3"
}
```

---

### 3.7 `POST /assessments/level-test`

설명:

- `answers`의 점수(1~5)를 합산해 0~100으로 정규화
- 레벨 판정:
  - `<40`: `beginner`
  - `<70`: `intermediate`
  - `>=70`: `advanced`
- 추천 과정을 반환하고 DB에 저장

요청 예시:

```json
{
  "lead_id": "lead-123",
  "answers": [
    { "area": "python", "score": 2 },
    { "area": "data", "score": 3 },
    { "area": "ai-concepts", "score": 2 }
  ],
  "additional_context": "비전공자이며 주 10시간 학습 가능합니다."
}
```

응답 예시:

```json
{
  "assessment_id": "18ffab52-d2f3-467e-a647-74f9fd9d553a",
  "level": "beginner",
  "score": 47,
  "recommended_course": "AI 기초 트랙 (파이썬/데이터 리터러시)",
  "mentoring_plan": "레벨 판정은 beginner이며...",
  "rag_context_ids": ["curriculum-catalog", "lead:lead-123", "call-memory"]
}
```

---

### 3.8 `GET /dashboard/metrics`

설명: 운영 대시보드 지표를 집계해 반환합니다.

쿼리 파라미터:

- `period_days` (선택, 기본 `7`, 범위 `7~90`): 시계열 구간(일)

응답 예시:

```json
{
  "total_leads": 8,
  "leads_with_calls": 5,
  "leads_with_assessments": 3,
  "conversion_rate": 0.625,
  "completion_rate": 0.6,
  "avg_assessment_score": 63.3,
  "queued_tasks": 1,
  "processing_tasks": 0,
  "failed_tasks": 0,
  "period_days": 14,
  "series": [
    { "date": "2026-03-24", "leads": 0, "calls": 0, "assessments": 0 },
    { "date": "2026-03-25", "leads": 1, "calls": 1, "assessments": 0 }
  ]
}
```

---

### 3.9 큐 조회/처리 API

#### 3.9.1 `GET /queue/tasks`

설명: 최근 큐 작업 목록을 조회합니다.

응답 예시:

```json
{
  "items": [
    {
      "task_id": "6e2cc339-0b1c-4f50-bf34-cf19a02247a0",
      "task_type": "stt_transcription",
      "status": "queued",
      "attempts": 0,
      "payload": {
        "recording_id": "02f2ef36-5fbe-4c97-bf80-f99ce9707fbb"
      },
      "result": null,
      "error_message": null,
      "created_at": "2026-04-06T07:11:22.000000+00:00",
      "updated_at": "2026-04-06T07:11:22.000000+00:00"
    }
  ]
}
```

#### 3.9.2 `POST /queue/process`

설명: 지정한 큐 작업을 즉시 처리합니다.

재시도 정책:

- 실패 시 `attempts + 1 < QUEUE_MAX_ATTEMPTS`이면 상태를 `queued`로 되돌려 재처리 대기
- 실패 시 한도 초과(`attempts >= QUEUE_MAX_ATTEMPTS`)이면 상태를 `failed`로 고정

요청 예시:

```json
{
  "task_id": "6e2cc339-0b1c-4f50-bf34-cf19a02247a0"
}
```

응답 예시:

```json
{
  "task_id": "6e2cc339-0b1c-4f50-bf34-cf19a02247a0",
  "status": "done",
  "result": {
    "transcript_id": "a3cbce5a-8e13-4f95-9af8-89ec2ea61d9d",
    "saved_turns": 2,
    "summary": "수강생 핵심 요청: ... / 상담 가이드: ..."
  },
  "error_message": null,
  "retry_queued": false
}
```

`status` 값:

| 값 | 의미 |
| --- | --- |
| `done` | 처리 완료 |
| `failed` | 처리 실패 |

#### 3.9.3 `POST /queue/workers/run`

설명: 큐 워커를 배치 실행해 대기중(`queued`) 작업을 순차 처리합니다.

요청 예시:

```json
{
  "limit": 5
}
```

응답 예시:

```json
{
  "requested_limit": 5,
  "processed": 2,
  "succeeded": 1,
  "failed": 0,
  "requeued": 1
}
```

---

### 3.10 `POST /documents/upload`

설명: 멘토링 지식 문서를 업로드합니다.

요청:

- `multipart/form-data`
- 필드: `file`

응답 예시:

```json
{
  "document_id": "35d64baa-b49d-4c44-b9af-cc4fb15b6708",
  "status": "knowledge_base_pending"
}
```

`status` 값:

| 값 | 의미 |
| --- | --- |
| `accepted` | PostgreSQL + pgvector 환경에서 임베딩/청크 저장까지 완료 |
| `knowledge_base_pending` | 문서 수신 완료, RAG 미설정 또는 색인 실패로 대기 |

---

## 4. 데이터 저장 모델(요약)

| 테이블 | 용도 |
| --- | --- |
| `leads` | 상담 신청 리드 정보 |
| `calls` | 콜 요청 및 스크립트 정보 |
| `call_transcript_turns` | 통화 전사 turn 데이터 |
| `assessments` | 레벨 평가 결과 |
| `knowledge_documents` | 업로드 문서 메타데이터 |
| `knowledge_document_chunks` | 문서 청크 및 pgvector 임베딩 |
| `recordings` | 업로드된 통화 녹취 메타데이터 |
| `async_tasks` | 비동기 큐 작업 상태/결과 |

---

## 5. 테스트 항목

### 5.1 API 계약 테스트(Integration)

- `test_lead_registration_requires_consent`
- `test_lead_registration_returns_contract_shape`
- `test_call_request_requires_non_empty_question`
- `test_call_request_returns_draft_when_unconfigured`
- `test_recording_upload_enqueues_transcription_task`
- `test_queue_process_returns_contract_shape`
- `test_queue_worker_run_returns_contract_shape`
- `test_transcript_ingest_returns_contract_shape`
- `test_tts_preview_returns_audio_metadata`
- `test_level_assessment_returns_recommended_course`
- `test_dashboard_metrics_returns_contract_shape`
- `test_document_upload_returns_contract_shape`
- `test_document_upload_requires_file`
- `test_health`

실행 명령:

```bash
cd backend
python -m pytest -m integration -q
```

### 5.2 단계별 권장 실행 순서

```bash
cd backend
python -m pytest -m unit -q
python -m pytest -m smoke -q
python -m pytest -m integration -q
```

전체 상세 규칙은 `docs/testing-strategy.md`를 참고합니다.
