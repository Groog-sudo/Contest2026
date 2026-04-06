# Architecture Overview

## 목표

이 프로젝트는 교육 현장에서 사용하는 문서와 질의응답 흐름을 AI 기반으로 연결하는 RAG 어시스턴트의 최소 실행 구조를 제공합니다.

## 구성

### Frontend

- React + JavaScript + Vite
- TailwindCSS 기반 단일 페이지 UI
- 문서 업로드, 질문 입력, 응답/출처 표시, 설정 안내 제공

### Backend

- FastAPI REST API
- 설정 관리: `app/core/config.py`
- API 라우팅: `app/api/v1`
- 스키마: `app/schemas`
- 서비스 레이어: `app/services`
- RAG 준비형 모듈: `app/rag`
- Pinecone 연동 준비형 클라이언트: `app/clients`

## 데이터 흐름

1. 사용자가 문서를 업로드한다.
2. 백엔드는 추후 `loader -> chunker -> embedding -> retriever` 흐름으로 확장 가능하도록 설계되어 있다.
3. 사용자가 질문을 입력한다.
4. 백엔드는 관련 문맥을 검색하고 생성 모델에 전달하는 구조로 발전시킬 수 있다.

## 현재 상태

- API 키가 없어도 전체 앱이 구동된다.
- RAG 미설정 상태에서는 안내형 메시지를 반환한다.
- 실제 Pinecone 업로드/조회와 생성 모델 호출은 다음 단계 구현 대상으로 분리되어 있다.
