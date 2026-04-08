# 테스트 전략 명세서 (Unit -> Smoke -> Integration)

> 프로젝트: AI 전화 멘토링 시스템  
> 최종 수정일: `2026-04-08`  
> 목적: 배포 전 테스트를 단계적으로 수행해 빠르게 실패를 감지하고, 통합 리스크를 마지막에 검증

---

## 1. 테스트 플로우

기본 실행 순서:

1. Unit Test
2. Smoke Test
3. Integration Test

운영 원칙:

- 앞 단계 실패 시 다음 단계를 실행하지 않습니다.
- Unit/Smoke는 빠른 피드백, Integration은 실제 흐름 검증에 집중합니다.

---

## 2. 단계별 범위

### 2.1 Unit Test

목적:

- 순수 로직, 경계값, 파싱 규칙 검증

현재 대상:

- `backend/tests/test_unit_service_utils.py`
  - 레벨 판정 경계값
  - 전사 speaker 정규화
  - 요약 문자열 생성

실행 명령:

```bash
cd backend
python -m pytest -m unit -q
```

---

### 2.2 Smoke Test

목적:

- 앱이 정상 기동하고 핵심 경로가 즉시 사용 가능한지 최소 검증

현재 대상:

- `backend/tests/test_health.py`
- Frontend 빌드 확인 (`npm run build`)
- PostgreSQL 프로필 사용 시 `backend/.env`의 `APP_DATABASE_URL`이 `vector` 확장이 활성화된 실행 중 인스턴스를 가리키는지 사전 확인

실행 명령:

```bash
cd backend
python -m pytest -m smoke -q

cd ../frontend
npm run build
```

---

### 2.3 Integration Test

목적:

- API 계약, DB 저장, 큐 처리, 대시보드 집계 등 다중 컴포넌트 상호작용 검증

현재 대상:

- `backend/tests/test_api_contract.py`

검증 항목 예:

- 리드/콜/전사/TTS/레벨테스트 API 계약
- 녹취 업로드 -> 큐 등록 -> 처리 응답
- 대시보드 `period_days` 시계열 응답 형식

실행 명령:

```bash
cd backend
python -m pytest -m integration -q
```

---

## 3. 전체 파이프라인 실행 명령

로컬에서 권장 순서:

```bash
cd backend
# backend/.env -> APP_DATABASE_URL 확인
python -m pytest -m unit -q
python -m pytest -m smoke -q
python -m pytest -m integration -q

cd ../frontend
npm run build
```

전체 백엔드 회귀(마커 무시):

```bash
cd backend
python -m pytest -q
```

---

## 4. 테스트 분류 규칙

| 분류 | 기준 | 예시 |
| --- | --- | --- |
| `unit` | 외부 I/O 없이 함수/메서드 로직 중심 | 점수 경계값, 텍스트 파싱 |
| `smoke` | 핵심 경로 최소 생존 확인 | `/health`, 프론트 빌드 |
| `integration` | API+DB+큐 등 계층 결합 검증 | 계약 테스트, 큐 워커 결과 |

---

## 5. CI 적용 가이드

권장 Job Gate:

1. `unit` job
2. `smoke` job
3. `integration` job
4. `frontend-build` job

조건:

- `unit` 성공 시에만 `smoke`
- `smoke` 성공 시에만 `integration`
- `integration` 성공 시에만 배포 승인 단계 진입

---

## 6. 향후 확장

1. Frontend 컴포넌트 테스트(Vitest + RTL) 추가 후 `unit`에 편입
2. 실 STT/TTS provider 환경 분리 integration suite 추가
3. 큐 재시도 한도(`QUEUE_MAX_ATTEMPTS`) 경계 케이스 전용 테스트 분리
