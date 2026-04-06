# Contest2026

AI 활용 차세대 교육 솔루션 공모전을 위한 RAG 기반 교육 어시스턴트 모노레포입니다.

현재 스캐폴드는 `React + JavaScript + Vite + TailwindCSS` 프론트엔드와 `FastAPI` 백엔드, 그리고 Pinecone 기반 RAG 확장을 위한 기본 모듈 구조를 포함합니다.

## 프로젝트 개요

- 공모전 주제: AI 활용 차세대 교육 솔루션
- 프로젝트 방향: 교육 문서 업로드, 질문 입력, 답변/출처 확인이 가능한 RAG 어시스턴트
- 주요 대상: 수강생, 강사, 교육 운영자
- 현재 상태: API 키 없이도 프론트/백엔드 실행 가능, RAG 관련 API는 미설정 시 안내형 응답 반환

## 주요 기능

- 교육용 문서 업로드 UI 및 업로드 API 기본 구조
- 질문 입력, 응답 표시, 출처 표시가 가능한 단일 페이지 UI
- `GET /api/v1/health`, `POST /api/v1/chat/query`, `POST /api/v1/documents/upload` 제공
- Pinecone, OpenAI, RAG 파이프라인 확장을 위한 백엔드 모듈 분리
- 공모전 제출 문서 작성을 위한 초안 문서 포함

## 디렉터리 구조

```text
Contest2026/
|-- docs/
|   |-- architecture.md
|   `-- ai-report-outline.md
|-- frontend/
|   |-- src/
|   |-- package.json
|   `-- .env.example
|-- backend/
|   |-- app/
|   |-- tests/
|   |-- requirements.txt
|   `-- .env.example
|-- .env.example
`-- README.md
```

- `docs/`: 아키텍처 설명과 AI 리포트 초안
- `frontend/`: 사용자 화면과 API 호출 로직
- `backend/`: FastAPI 서버, 스키마, 서비스, RAG 준비형 모듈, 테스트

## 날짜별 작업 기록

| 날짜 | 담당 | 작업 내용 | 관련 파일/링크 | 비고 |
| --- | --- | --- | --- | --- |
| 2026-04-06 | AI | 공모전용 AI 교육 RAG 모노레포 기본 스캐폴드 구성<br>루트 문서, FastAPI API, React UI, 테스트 구조 생성 | [`README.md`](README.md)<br>[`frontend/src/App.jsx`](frontend/src/App.jsx)<br>[`backend/app/main.py`](backend/app/main.py)<br>[`backend/tests/test_chat_contract.py`](backend/tests/test_chat_contract.py) | 초기 구조 생성 |
| 2026-04-06 | AI | 프론트엔드 언어를 TypeScript에서 JavaScript로 전환<br>빌드 및 백엔드 테스트 검증 완료 | [`frontend/package.json`](frontend/package.json)<br>[`frontend/src/main.jsx`](frontend/src/main.jsx)<br>[`frontend/src/lib/api.js`](frontend/src/lib/api.js)<br>[`backend/requirements.txt`](backend/requirements.txt) | `npm run build`, `pytest -q` 통과 |

### 새 항목 추가 템플릿

복사/붙여넣기용 1줄:

`| YYYY-MM-DD | 이름 | 작업 내용 | 관련 파일/링크 | 비고 |`

입력 규칙:

- 날짜는 `YYYY-MM-DD` 형식으로 작성합니다.
- 담당은 실명 또는 팀 내 합의된 표기로 통일합니다.
- 작업 내용은 한 줄 요약 후 필요하면 `<br>`로 세부 항목을 덧붙입니다.
- 관련 파일/링크는 가능한 범위에서 1~5개를 `[frontend/src/App.jsx](frontend/src/App.jsx)` 형식으로 연결합니다.

## 기술 스택

### Frontend ([`frontend/package.json`](frontend/package.json) 기반)

| 구분 | 기술 | 버전 | 비고 |
| --- | --- | --- | --- |
| 프레임워크 | React | ^19.2.0 | UI 라이브러리 |
| 렌더링 | React DOM | ^19.2.0 | 브라우저 렌더링 |
| 빌드/개발 서버 | Vite | ^7.1.10 | 개발 서버 및 번들러 |
| Vite 플러그인 | @vitejs/plugin-react | ^5.1.0 | React 지원 |
| 스타일링 | Tailwind CSS | ^4.1.4 | 유틸리티 CSS |
| Tailwind(Vite) | @tailwindcss/vite | ^4.1.4 | Vite 연동 |
| 언어 | JavaScript | ES Modules | 프론트엔드 구현 언어 |

### Backend ([`backend/requirements.txt`](backend/requirements.txt) 기반)

| 구분 | 기술 | 버전 | 비고 |
| --- | --- | --- | --- |
| 웹 프레임워크 | FastAPI | >=0.116,<1.0 | REST API 서버 |
| ASGI 서버 | Uvicorn[standard] | >=0.35,<1.0 | 로컬 실행 서버 |
| 설정 관리 | pydantic-settings | >=2.10,<3.0 | 환경 변수 관리 |
| 파일 업로드 | python-multipart | >=0.0.20,<1.0 | multipart 처리 |
| 테스트 | pytest | >=8.4,<9.0 | 백엔드 테스트 |
| HTTP 클라이언트/테스트 | httpx | >=0.28,<1.0 | API 테스트 보조 |

### AI / 데이터 설계

| 구분 | 기술 | 상태 | 비고 |
| --- | --- | --- | --- |
| 벡터 DB | Pinecone | 구조 반영 | 실제 SDK 연동은 다음 단계 |
| 검색 증강 생성 | RAG | 구조 반영 | `loader`, `chunker`, `retriever`, `generator` 모듈 분리 |
| 생성형 AI | OpenAI API | 환경 변수 준비 | 키 설정 전에는 안내형 응답 반환 |

## 실행 방법

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- 기본 주소: `http://localhost:5173`

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- 기본 주소: `http://localhost:8000`

## 환경 변수

루트 [`/.env.example`](.env.example)는 전체 구조 참고용이며, 실제 실행 시에는 각 워크스페이스 예시 파일을 기준으로 설정하면 됩니다.

- [`frontend/.env.example`](frontend/.env.example)
- [`backend/.env.example`](backend/.env.example)

| 변수명 | 위치 | 설명 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Frontend | 프론트엔드가 호출할 백엔드 주소 |
| `OPENAI_API_KEY` | Backend | 생성형 AI 모델 연동 키 |
| `PINECONE_API_KEY` | Backend | Pinecone 연동 키 |
| `PINECONE_INDEX_NAME` | Backend | Pinecone 인덱스 이름 |
| `PINECONE_NAMESPACE` | Backend | 기본 namespace |
| `FRONTEND_ORIGIN` | Backend | CORS 허용 프론트엔드 주소 |

## API 요약

| Method | Endpoint | 설명 | 현재 동작 |
| --- | --- | --- | --- |
| `GET` | `/api/v1/health` | 서버 상태 확인 | 항상 `{ "status": "ok" }` 반환 |
| `POST` | `/api/v1/chat/query` | 질문 기반 답변 요청 | 미설정 시 503 안내형 응답 |
| `POST` | `/api/v1/documents/upload` | 문서 업로드 | 미설정 시 `unconfigured` 상태 반환 |

## 문서 링크

- 아키텍처 설명: [`docs/architecture.md`](docs/architecture.md)
- AI 리포트 초안: [`docs/ai-report-outline.md`](docs/ai-report-outline.md)

## 검증 상태

- Frontend: `npm run build` 통과
- Backend: `pytest -q` 통과

## 다음 작업 제안

- 공모전에서 해결할 교육 현장 페인 포인트를 하나로 좁혀 시나리오 확정
- Pinecone 업로드/조회 및 실제 임베딩 로직 연결
- OpenAI 기반 답변 생성 로직 연결
- 학생, 강사, 운영자 관점의 역할별 화면과 워크플로우 추가
