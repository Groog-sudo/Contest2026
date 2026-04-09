# Architecture

> 버전: `0.5.0`  
> 마지막 수정일: `2026-04-09`  
> 상태: `Delivery Issue Domain 적용 완료`

## 1. 개요/목표

본 아키텍처는 배달 주문 이슈 접수/분류/전달 자동화를 목적으로 하며, 다음을 보장합니다.

1. 고객 인입부터 이슈 분석까지 단일 플로우
2. PostgreSQL(정형) + ChromaDB(벡터) 이중 저장 구조
3. STT/TTS/Queue 연계 확장 가능한 파이프라인

## 2. 현재 구현 범위

- Frontend: 리드 접수, 콜 요청, 이슈 분석 확인, 지식 문서 업로드, 대시보드
- Backend API: leads / calls / analyses / documents / queue / dashboard / health
- Service: `backend/app/services/delivery_issue_service.py`
- Repository: `backend/app/db/repository.py`

## 3. 모듈 구성

| 레이어 | 책임 | 주요 파일 |
| --- | --- | --- |
| API | 요청/응답 계약 | `backend/app/api/v1/endpoints/*` |
| Service | 도메인 오케스트레이션 | `backend/app/services/delivery_issue_service.py` |
| Repository | DB 접근 및 집계 | `backend/app/db/repository.py` |
| RAG | 문서 로딩/청킹/검색 | `backend/app/rag/*` |
| External Client | STT/TTS/Storage | `backend/app/clients/*` |
| Worker | 큐 처리 | `backend/app/workers/queue_worker.py` |

## 4. API/데이터 흐름

1. `POST /leads/register`
2. `POST /calls/request`
3. (옵션) `POST /calls/recordings/upload` -> `async_tasks` 생성
4. `POST /calls/transcripts/ingest`
5. `POST /analyses/analyze` -> `incident_analyses` 저장
6. `GET /dashboard/metrics`로 운영 지표 확인

## 5. 데이터 저장 전략

### 5.1 PostgreSQL

- 운영 원장 데이터 저장
- 분석 결과는 `incident_analyses` 테이블에 저장
- 큐/전사/파일 메타데이터는 별도 테이블 유지

### 5.2 ChromaDB

- 문서 임베딩 저장 및 검색
- 컬렉션: `CHROMA_COLLECTION_NAME`
- 경로: `CHROMA_PERSIST_DIRECTORY`

## 6. 검증 상태

- Backend pytest 통과 (`19 passed`)
- Frontend build 통과
- 기준일: `2026-04-09`

## 7. 확장 계획

1. 멀티 모델 기반 분류 재검증 레이어 추가
2. 고위험 이슈 실시간 알림/티켓 연동
3. 운영 DB 마이그레이션 자동 적용(릴리즈 파이프라인)
