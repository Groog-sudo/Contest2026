# AI 리포트 작성 템플릿

> 공모전 제출용 템플릿  
> 버전: `0.5.0`  
> 마지막 수정일: `2026-04-09`

## 1. 메타 정보

- 프로젝트명:
- 팀명:
- 제출일:
- 버전:
- 데모 링크:
- 저장소 링크:

## 2. 개요/목표

- 해결하려는 문제:
- 대상 사용자:
- 핵심 목표(3줄 이내):

## 3. 현재 구현 범위

- [ ] 고객 불만 리드 접수
- [ ] 상담 스크립트 생성
- [ ] STT 전사 입력/저장
- [ ] 이슈 분석 JSON 생성
- [ ] 책임 주체별 전달 문안 생성
- [ ] 운영 대시보드 지표 조회
- [ ] 문서 RAG 업로드/검색

## 4. 시스템/API/데이터 흐름

### 4.1 주요 API

- `POST /api/v1/leads/register`
- `POST /api/v1/calls/request`
- `POST /api/v1/calls/transcripts/ingest`
- `POST /api/v1/analyses/analyze`
- `GET /api/v1/dashboard/metrics`

### 4.2 데이터 저장

- PostgreSQL: `leads`, `calls`, `incident_analyses`, `async_tasks` 등
- ChromaDB: 문서 임베딩 컬렉션

### 4.3 운영 DB 마이그레이션

- SQL: `backend/sql/migrations/20260409_postgres_legacy_schema_to_delivery_issue.sql`
- 가이드: `backend/sql/migrations/README.md`

## 5. 환경 변수/실행 환경

- DB: `APP_DATABASE_URL`, `APP_DB_PATH`
- Chroma: `CHROMA_PERSIST_DIRECTORY`, `CHROMA_COLLECTION_NAME`
- AI: `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_STT_MODEL`, `OPENAI_TTS_MODEL`
- Queue/Storage: `QUEUE_*`, `OBJECT_STORAGE_*`

## 6. 테스트/검증 상태

- Backend: `python -m pytest -q` 결과
- Frontend: `npm run build` 결과
- 기준일:

## 7. 확장 계획

1. 분류 정확도 개선(룰 + LLM 앙상블)
2. 고위험 이슈 실시간 알림
3. 운영 시스템 연동(티켓/CRM)
4. 정책 문서 버전 기반 RAG 개선

## 8. 참고 문서

- 아키텍처: `docs/architecture.md`
- API 명세: `docs/api-specification.md`
- 미디어 파이프라인: `docs/media-pipeline-spec.md`
- 테스트 전략: `docs/testing-strategy.md`
