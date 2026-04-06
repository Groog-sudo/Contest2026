# 시스템 아키텍처 명세서

> 프로젝트: AI 활용 차세대 교육 솔루션 - AI 전화 멘토링 시스템  
> 버전: `0.3.0`  
> 최종 수정일: `2026-04-06`  
> 상태: STT/TTS/DB/레벨평가 스캐폴드 반영 완료

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
│  │  /calls/transcripts/ingest /calls/tts/preview             │    │
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
│  │  - assessments       │   │ - Call provider (planned)      │   │
│  │  - knowledge_docs    │   │                                │   │
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

---

## 4. 핵심 컴포넌트

### 4.1 MentoringService

- 리드 등록 후 DB 저장
- 콜 스크립트 생성 및 상태 판정 (`drafted`, `script_ready`, `queued`)
- 전사 텍스트를 turn 단위로 저장하고 요약 생성
- 레벨 테스트 점수 정규화 후 추천 과정 생성
- TTS 프리뷰 URL 생성

### 4.2 MentoringRepository (SQLite)

초기 실행 시 스키마를 자동 생성합니다.

- `leads`
- `calls`
- `call_transcript_turns`
- `assessments`
- `knowledge_documents`

### 4.3 STT/TTS Client

- 현재 `mock` 프로바이더로 동작
- 실 서비스 연동 시 해당 클래스 내부 구현만 교체 가능

---

## 5. 데이터 흐름

### 5.1 리드 접수

`LeadCapturePanel -> POST /leads/register -> leads 저장`

### 5.2 콜 요청

`CallRequestPanel -> POST /calls/request -> calls 저장 -> 스크립트/근거 반환`

### 5.3 통화 전사 적재

`POST /calls/transcripts/ingest -> STT/전사 파싱 -> call_transcript_turns 저장`

### 5.4 레벨 평가 및 추천

`POST /assessments/level-test -> 점수 정규화 -> 레벨 판정 -> assessments 저장`

### 5.5 TTS 프리뷰

`POST /calls/tts/preview -> 음성 URL 메타데이터 반환`

---

## 6. 환경 변수 설계

| 그룹 | 변수 |
| --- | --- |
| DB | `APP_DB_PATH` |
| RAG | `OPENAI_API_KEY`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`, `PINECONE_NAMESPACE` |
| STT | `STT_PROVIDER_NAME`, `STT_PROVIDER_API_KEY` |
| TTS | `TTS_PROVIDER_NAME`, `TTS_PROVIDER_API_KEY` |
| Call | `CALL_PROVIDER_NAME`, `CALL_PROVIDER_API_KEY`, `OUTBOUND_CALL_FROM_NUMBER` |
| Common | `FRONTEND_ORIGIN` |

---

## 7. 현재 한계

- 실제 STT/TTS/통신사 API 호출은 미연동 (`mock` 동작)
- 추천 로직은 규칙 기반(점수 구간)이며 학습형 모델은 미적용
- 대화 히스토리 요약 고도화 및 검색 가중치 조정 미적용

---

## 8. 확장 계획

1. 실 STT/TTS 프로바이더 연동
2. 녹취 원본 저장소(S3/Blob) 및 비동기 처리 큐 도입
3. 상담 메모리 + 커리큘럼 하이브리드 RAG 검색 고도화
4. 추천 결과의 상담 전환율/학습 지속률 지표화
