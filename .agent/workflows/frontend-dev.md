---
description: 프론트엔드 개발 서버 실행 및 빌드 검증
---

# 프론트엔드 실행 가이드

## 1. 개발 서버 실행

```bash
cd frontend
npm install
```

// turbo
```bash
cd frontend && npm run dev
```

- 기본 주소: `http://localhost:5173`
- API 주소: `frontend/.env`의 `VITE_API_BASE_URL`

## 2. 빌드 검증

// turbo
```bash
cd frontend && npm run build
```

- 에러 없이 `dist/` 생성 시 성공

## 3. 현재 화면 구조

- `features/leads/LeadCapturePanel.jsx`
- `features/calls/CallRequestPanel.jsx`
- `features/knowledge/KnowledgeBasePanel.jsx`
- `features/status/SetupGuide.jsx`

## 4. API 호출 위치

모든 API 호출은 `frontend/src/lib/api.js`에서 관리합니다.

현재 포함 함수:

- `registerLead`
- `requestMentoringCall`
- `ingestCallTranscript`
- `previewCallTts`
- `evaluateLevelTest`
- `uploadKnowledgeDocument`
- `fetchHealth`

## 5. 구현 원칙

- 공통 컴포넌트: `src/components/`
- 기능 컴포넌트: `src/features/`
- API 타입 JSDoc: `src/types/api.js`
- 에러는 `ApiRequestError`로 통일 처리
