# 음성 파이프라인 상세 명세서 (STT/TTS/Storage/Queue)

> 프로젝트: AI 활용 차세대 교육 솔루션 - AI 전화 멘토링 시스템  
> 버전: `0.3.0`  
> 최종 수정일: `2026-04-08`  
> 대상 코드 기준: `backend/app/clients/*`, `backend/app/services/mentoring_service.py`, `backend/app/workers/queue_worker.py`

---

## 1. 문서 목적

본 문서는 아래 음성 처리 파이프라인의 실제 구현 동작을 코드 기준으로 명세합니다.

1. 녹취 업로드
2. 오브젝트 저장
3. STT 전사 큐 등록/처리
4. 전사 결과 DB 저장
5. TTS 프리뷰 생성/저장

---

## 2. 구성 컴포넌트

| 계층 | 컴포넌트 | 주요 파일 | 역할 |
| --- | --- | --- | --- |
| API | Calls Endpoint | `backend/app/api/v1/endpoints/calls.py` | 녹취 업로드, TTS 프리뷰 API |
| API | Queue Endpoint | `backend/app/api/v1/endpoints/queue.py` | 큐 단건 처리, 워커 배치 실행 |
| Service | MentoringService | `backend/app/services/mentoring_service.py` | 음성 파이프라인 오케스트레이션 |
| Client | STTClient | `backend/app/clients/stt_client.py` | 음성 -> 텍스트 전사 |
| Client | TTSClient | `backend/app/clients/tts_client.py` | 텍스트 -> 음성 합성 |
| Client | ObjectStorageClient | `backend/app/clients/storage_client.py` | 오디오 바이트 저장/조회 |
| Worker | Queue Worker | `backend/app/workers/queue_worker.py` | 큐 배치 처리 실행 |
| Data | Repository | `backend/app/db/repository.py` | PostgreSQL 우선/SQLite fallback으로 recordings/async_tasks/transcript turns 저장 |

---

## 3. STT 상세 명세

### 3.1 지원 프로바이더

| `STT_PROVIDER_NAME` 값 | 동작 | 비고 |
| --- | --- | --- |
| `mock` | 고정된 2줄 전사 텍스트 반환 | 개발/데모 기본값 |
| `openai` | OpenAI Audio Transcription 호출 | `OPENAI_STT_MODEL` 사용 |
| 기타 값 | placeholder 텍스트 반환 | `"STT provider response placeholder"` |

### 3.2 입력 우선순위

`STTClient.transcribe()` 입력 처리 우선순위:

1. `audio_bytes`가 있으면 그대로 사용
2. `audio_bytes`가 없고 `recording_url`이 있으면 HTTP 다운로드 후 사용
3. 둘 다 없으면 예외 발생 (`openai` 모드)

다운로드 조건:

- HTTP 클라이언트: `httpx`
- timeout: `30.0s`
- redirect follow: `true`

### 3.3 API Key 및 모델 결정

OpenAI STT 호출 시 키 우선순위:

1. `STT_PROVIDER_API_KEY`
2. `OPENAI_API_KEY`

모델:

- `OPENAI_STT_MODEL` (기본값: `gpt-4o-mini-transcribe`)

### 3.4 결과 형식

전사 후 시스템 내부 표준 텍스트 형식:

```text
student: ...
ai: ...
```

후속 파싱 규칙:

- `prefix: message` 구조에서 `prefix`를 화자로 해석
- 허용 화자: `student`, `ai`, `counselor`
- 기타 화자는 `student`로 정규화

---

## 4. TTS 상세 명세

### 4.1 지원 프로바이더

| `TTS_PROVIDER_NAME` 값 | 동작 | 반환 MIME |
| --- | --- | --- |
| `mock` | `"MOCK_TTS_PREVIEW:" + URL-encoded(script[:80])` 바이트 생성 | `audio/mpeg` |
| `openai` | OpenAI Audio Speech 호출 | `audio/mpeg` |
| 기타 값 | placeholder 바이트 반환 | `audio/mpeg` |

### 4.2 API Key 및 모델 결정

OpenAI TTS 호출 시 키 우선순위:

1. `TTS_PROVIDER_API_KEY`
2. `OPENAI_API_KEY`

모델:

- `OPENAI_TTS_MODEL` (기본값: `gpt-4o-mini-tts`)

호출 파라미터:

- `voice`: 요청값 사용 (API 기본 `mentor-ko`)
- `input`: script 본문
- `response_format`: `mp3`

### 4.3 응답 바이트 처리

OpenAI SDK 응답 처리 순서:

1. `response.content` 속성이 있으면 사용
2. `response.read()` 메서드가 있으면 사용
3. 둘 다 없으면 예외 발생

---

## 5. 오브젝트 저장소 상세 명세

### 5.1 지원 저장소

| `OBJECT_STORAGE_PROVIDER` 값 | 저장 방식 | URL 반환 |
| --- | --- | --- |
| `local` | `OBJECT_STORAGE_LOCAL_DIR` 하위 파일 저장 | `local://{key}` 또는 `OBJECT_STORAGE_PUBLIC_BASE_URL/{key}` |
| `s3` | `boto3`로 `put_object/get_object` | `s3://bucket/key` 또는 `OBJECT_STORAGE_PUBLIC_BASE_URL/{key}` |

### 5.2 녹취/프리뷰 키 규칙

- 녹취: `recordings/{lead_id}/{call_id}/{uuid}{ext}`
- TTS 프리뷰: `tts-previews/{uuid}.mp3`

### 5.3 필수 조건

`s3` 모드에서 필수:

- `OBJECT_STORAGE_BUCKET`

선택(환경별):

- `OBJECT_STORAGE_REGION`
- `OBJECT_STORAGE_ENDPOINT_URL`
- `OBJECT_STORAGE_ACCESS_KEY`
- `OBJECT_STORAGE_SECRET_KEY`

---

## 6. 큐/워커 처리 명세

### 6.1 큐 생성

`POST /api/v1/calls/recordings/upload` 처리 시:

1. 오디오를 저장소에 저장
2. `recordings` 테이블에 메타데이터 저장
3. `async_tasks`에 `task_type=stt_transcription` 작업 생성 (`status=queued`)

작업 payload 필드:

- `recording_id`
- `call_id`
- `lead_id`
- `object_key`
- `content_type`
- `filename`

### 6.2 자동 처리

`QUEUE_AUTO_PROCESS=true`이면 업로드 직후 BackgroundTask로 아래 함수가 호출됩니다.

- `run_queue_worker_once(settings, limit=1)`

### 6.3 단건 처리 상태 전이

`process_queue_task(task_id)` 상태 전이:

1. `done`이면 기존 결과 즉시 반환
2. `processing`이면 중복 처리 방지 실패 반환
3. `attempts >= QUEUE_MAX_ATTEMPTS`이면 즉시 `failed`
4. 그 외 `queued/failed` 상태는 `processing`으로 전환 후 실행

실행 실패 시 재시도 규칙:

- `(attempts + 1) < QUEUE_MAX_ATTEMPTS`이면 `queued`로 되돌림 (`retry_queued=true`)
- 아니면 `failed` 고정 (`retry_queued=false`)

### 6.4 배치 처리

`POST /api/v1/queue/workers/run`

- 입력: `limit` (기본 10, 범위 1~100)
- 처리 대상: `status=queued` 작업, 생성 시각 오름차순
- 응답 집계:
  - `processed`
  - `succeeded`
  - `requeued`
  - `failed`

---

## 7. 데이터 저장 명세 (음성 관련)

### 7.1 `recordings`

| 컬럼 | 의미 |
| --- | --- |
| `recording_id` | 녹취 식별자 |
| `call_id` | 콜 식별자 |
| `lead_id` | 리드 식별자 |
| `object_key` | 저장소 키 |
| `content_type` | MIME 타입 |
| `size_bytes` | 파일 크기 |
| `created_at` | 생성 시각 (UTC ISO) |

### 7.2 `async_tasks`

| 컬럼 | 의미 |
| --- | --- |
| `task_id` | 작업 식별자 |
| `task_type` | 작업 타입 (`stt_transcription`) |
| `payload_json` | 작업 입력 JSON |
| `status` | `queued` / `processing` / `done` / `failed` |
| `result_json` | 성공 결과 JSON |
| `error_message` | 실패 메시지 |
| `attempts` | 처리 시도 횟수 |
| `created_at`, `updated_at` | 생성/갱신 시각 |

### 7.3 `call_transcript_turns`

STT 처리 성공 시 turn 단위로 저장됩니다.

| 컬럼 | 의미 |
| --- | --- |
| `turn_id` | turn 식별자 |
| `transcript_id` | 전사 묶음 식별자 |
| `call_id` | 콜 식별자 |
| `lead_id` | 리드 식별자 |
| `speaker` | `student` / `ai` / `counselor` |
| `utterance` | 발화 텍스트 |
| `turn_index` | turn 순서 |

---

## 8. 예외 및 장애 처리

| 구간 | 실패 원인 | 처리 방식 |
| --- | --- | --- |
| STT(OpenAI) | API Key 누락 | RuntimeError |
| STT(OpenAI) | audio source 없음 | RuntimeError |
| Storage(s3) | bucket 누락 | RuntimeError |
| Queue | 한도 초과 재시도 | `failed` 고정 |
| Queue | 일시 오류 | `queued` 재배치 가능 |

---

## 9. 운영 권장값

| 환경 | STT | TTS | Storage | Queue |
| --- | --- | --- | --- | --- |
| 로컬 개발 | `mock` | `mock` | `local` | `QUEUE_AUTO_PROCESS=true` |
| 스테이징 | `openai` | `openai` | `s3` 또는 S3-compatible | `QUEUE_AUTO_PROCESS=false` + 스케줄러 워커 |
| 운영 | `openai` 또는 상용 STT | `openai` 또는 상용 TTS | `s3` | 외부 워커 상시 구동 |

---

## 10. 검증 포인트

1. 녹취 업로드 시 `recordings`/`async_tasks` 레코드 생성 확인
2. `queue/workers/run` 호출 시 `processed/succeeded/requeued/failed` 집계 확인
3. STT 결과 turn 파싱 후 `call_transcript_turns` 적재 확인
4. `calls/tts/preview` 응답 `audio_url`, `mime_type` 확인
5. `QUEUE_MAX_ATTEMPTS` 경계값에서 재시도/최종 실패 상태 확인
