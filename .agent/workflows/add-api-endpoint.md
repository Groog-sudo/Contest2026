---
description: 새 API 엔드포인트를 추가하는 표준 절차
---

# API 엔드포인트 추가 절차

## 1. 스키마 정의

`backend/app/schemas/{feature}.py`에 요청/응답 모델을 작성합니다.

```python
from pydantic import BaseModel, Field

class MyRequest(BaseModel):
    value: str = Field(..., min_length=1)

class MyResponse(BaseModel):
    result: str
```

## 2. 서비스 로직 작성

`backend/app/services/`에 비즈니스 로직을 작성합니다.

```python
class MyService:
    def process(self, payload: MyRequest) -> MyResponse:
        ...
```

## 3. 저장이 필요한 경우 Repository 반영

영속화가 필요하면 `backend/app/db/repository.py`에 메서드와 스키마를 추가합니다.

원칙:

- 테이블 생성: `_ensure_schema()`
- 저장/조회 메서드 분리
- 엔드포인트에서 SQL 직접 호출 금지

## 4. 엔드포인트 작성

`backend/app/api/v1/endpoints/{feature}.py`

```python
from fastapi import APIRouter, Depends
from app.core.config import Settings, get_settings

router = APIRouter()

@router.post("/my-endpoint", response_model=MyResponse)
async def my_endpoint(
    payload: MyRequest,
    settings: Settings = Depends(get_settings),
) -> MyResponse:
    service = MyService(settings)
    return service.process(payload)
```

## 5. 라우터 등록

`backend/app/api/v1/router.py`에 등록합니다.

```python
api_router.include_router(my_feature.router, prefix="/my-feature", tags=["my-feature"])
```

## 6. 테스트 작성

`backend/tests/test_api_contract.py`에 계약 테스트를 추가합니다.

기본 검증:

- 성공 케이스 (`200`)
- 입력 검증 실패 (`422`)
- 응답 shape

## 7. 문서 갱신

- `docs/api-specification.md`
- `docs/architecture.md` (흐름/모듈 변경 시)
- `README.md` (API 요약/상태)

## 8. 검증

// turbo
```bash
cd backend && .venv\Scripts\python -m pytest -q
```
