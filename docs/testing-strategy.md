# 테스트 전략 (Unit -> Smoke -> Integration)

> 프로젝트: 배달 불만 접수 AI 상담사  
> 최종 수정일: `2026-04-09`

---

## 1. 실행 순서

1. Unit
2. Smoke
3. Integration

앞 단계 실패 시 다음 단계로 진행하지 않습니다.

---

## 2. 단계별 범위

### 2.1 Unit

- 파일: `backend/tests/test_unit_service_utils.py`
- 검증:
  - 전사 speaker 정규화
  - 요약 생성
  - 분류 규칙 핵심 케이스
  - 설정/저장소 플래그

실행:

```bash
cd backend
python -m pytest -m unit -q
```

### 2.2 Smoke

- 파일: `backend/tests/test_health.py`
- 목적: 앱 기동/핵심 헬스체크

실행:

```bash
cd backend
python -m pytest -m smoke -q

cd ../frontend
npm run build
```

### 2.3 Integration

- 파일: `backend/tests/test_api_contract.py`
- 검증:
  - 불만 접수/콜 요청/전사/TTS/분석 API 계약
  - 녹취 업로드 -> 큐 등록/처리
  - 대시보드 응답 구조

실행:

```bash
cd backend
python -m pytest -m integration -q
```

---

## 3. 전체 권장 명령

```bash
cd backend
python -m pytest -m unit -q
python -m pytest -m smoke -q
python -m pytest -m integration -q

cd ../frontend
npm run build
```

---

## 4. 참고 사항

1. 테스트는 기본적으로 SQLite fallback을 사용해 로컬 의존성을 줄입니다.
2. PostgreSQL/ChromaDB 실환경 검증은 별도 시나리오로 추가하는 것을 권장합니다.
