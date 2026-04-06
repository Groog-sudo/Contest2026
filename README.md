# Contest2026

AI 활용 차세대 교육 솔루션 공모전을 위한 연락처 기반 AI 전화 멘토링 프로젝트 모노레포입니다.

| 항목 | 내용 |
| --- | --- |
| 버전 | `0.3.0` |
| 최종 수정일 | `2026-04-06` |
| 현재 상태 | 리드 접수/콜 요청/STT 전사 저장/TTS 프리뷰/레벨테스트 추천 스캐폴드 구현 완료 |

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
- `POST /api/v1/calls/transcripts/ingest`
- `POST /api/v1/calls/tts/preview`
- `POST /api/v1/assessments/level-test`
- `POST /api/v1/documents/upload`

### 데이터 저장

- SQLite 저장소 추가 (`APP_DB_PATH`)
- 저장 테이블:
  - `leads`
  - `calls`
  - `call_transcript_turns`
  - `assessments`
  - `knowledge_documents`

### AI/통신 확장 포인트

- STT 클라이언트 스텁: `backend/app/clients/stt_client.py`
- TTS 클라이언트 스텁: `backend/app/clients/tts_client.py`
- 통신사 발신 연동은 환경 변수 기반 구조만 반영 (실 호출은 후속 구현)

## 3. 디렉터리 구조

```text
Contest2026/
├── docs/
│   ├── architecture.md
│   ├── api-specification.md
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
| `APP_DB_PATH` | Backend | SQLite 파일 경로 |
| `OPENAI_API_KEY` | Backend | 생성형 AI 연동 키 |
| `PINECONE_API_KEY` | Backend | Pinecone 연동 키 |
| `PINECONE_INDEX_NAME` | Backend | Pinecone 인덱스 이름 |
| `PINECONE_NAMESPACE` | Backend | Pinecone namespace |
| `STT_PROVIDER_NAME` | Backend | STT 프로바이더 식별자 |
| `STT_PROVIDER_API_KEY` | Backend | STT API 키 |
| `TTS_PROVIDER_NAME` | Backend | TTS 프로바이더 식별자 |
| `TTS_PROVIDER_API_KEY` | Backend | TTS API 키 |
| `CALL_PROVIDER_NAME` | Backend | 발신 프로바이더 식별자 |
| `CALL_PROVIDER_API_KEY` | Backend | 발신 API 키 |
| `OUTBOUND_CALL_FROM_NUMBER` | Backend | 발신 번호 |
| `FRONTEND_ORIGIN` | Backend | CORS 허용 오리진 |

## 5. 실행 방법

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 6. 검증 상태

- Frontend: `npm run build` 통과
- Backend: `pytest -q` 통과 (`10 passed`)

## 7. 문서 링크

- 아키텍처: [`docs/architecture.md`](docs/architecture.md)
- API 명세: [`docs/api-specification.md`](docs/api-specification.md)
- AI 리포트 템플릿: [`docs/ai-report-outline.md`](docs/ai-report-outline.md)

## 8. 날짜별 작업 기록

| 날짜 | 담당 | 작업 내용 | 비고 |
| --- | --- | --- | --- |
| 2026-04-06 | AI | 프로젝트 초기 스캐폴드 구성 (Frontend/Backend/문서) | 기본 구조 |
| 2026-04-06 | AI | 리드 접수/콜 요청 중심으로 도메인 전환 | 교육 RAG 데모에서 상담 도메인으로 전환 |
| 2026-04-06 | AI | STT/TTS/상담기록 DB 연동 기반 백엔드 확장<br>`/api/v1/calls/transcripts/ingest`, `/api/v1/calls/tts/preview`, `/api/v1/assessments/level-test` 추가<br>SQLite Repository(`leads`, `calls`, `call_transcript_turns`, `assessments`, `knowledge_documents`) 반영 | `pytest -q` 10개 통과 |
| 2026-04-06 | AI | 문서/운영 워크플로우 동기화<br>`README.md`, `docs/architecture.md`, `docs/api-specification.md`, `docs/ai-report-outline.md`를 최신 설계로 갱신<br>`.agent/workflows/*`를 STT/TTS/DB/레벨평가 기준으로 업데이트 | `npm run build` 통과 |

## 9. 다음 단계 제안

1. 실 STT/TTS 프로바이더 SDK 연동
2. 통화 녹취 원본 저장소(S3/Blob) 및 비동기 처리 큐 도입
3. 커리큘럼 문서 + 상담 메모리 하이브리드 RAG 검색 고도화
4. 추천 결과의 전환율/완주율 지표 추적 대시보드 추가
