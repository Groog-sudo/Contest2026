---
description: 새 프론트엔드 기능(Feature) 컴포넌트를 추가하는 표준 절차
---

# 프론트엔드 기능 추가 절차

## 1. 기능 폴더 생성

`frontend/src/features/{feature}/`에 기능 단위로 배치합니다.

예시:

```text
frontend/src/features/{feature}/
├── {Feature}Panel.jsx
└── {Feature}Form.jsx
```

## 2. API 함수 추가

`frontend/src/lib/api.js`에 백엔드 호출 함수를 추가합니다.

```javascript
export async function callMyFeatureApi(payload) {
  const response = await fetch(`${API_BASE_URL}/api/v1/my-feature/endpoint`, {
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
    method: 'POST',
  });
  return parseResponse(response);
}
```

규칙:

- `parseResponse()` 사용
- 에러는 `ApiRequestError`로 처리
- 엔드포인트 문자열 하드코딩 중복 금지

## 3. 타입 문서화

새 요청/응답 타입은 `frontend/src/types/api.js`에 JSDoc으로 추가합니다.

## 4. 앱 통합

`frontend/src/App.jsx` 또는 기존 Feature panel에 import 후 배치합니다.

## 5. UI 원칙

- 기존 디자인 톤 유지
- 텍스트/상태 메시지 명확히 표현
- 로딩/성공/실패 상태를 분리해서 표시

## 6. 검증

// turbo
```bash
cd frontend && npm run build
```
