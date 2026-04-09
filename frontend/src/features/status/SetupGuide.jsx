const statusLabel = {
  checking: '백엔드 상태 확인 중',
  online: '백엔드 연결 완료',
  offline: '백엔드 미연결',
};

export default function SetupGuide({ apiBaseUrl, backendStatus }) {
  return (
    <section className="rounded-[28px] border border-white/10 bg-white/8 p-6 shadow-xl shadow-slate-950/20 backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-white">설정 안내</h2>
        <span className="rounded-full border border-white/10 bg-slate-950/35 px-3 py-1 text-xs font-medium text-slate-200">
          {statusLabel[backendStatus]}
        </span>
      </div>

      <div className="mt-4 space-y-4 text-sm leading-6 text-slate-300">
        <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4">
          <p className="font-medium text-white">기본 연결 정보</p>
          <p className="mt-2">API Base URL: {apiBaseUrl}</p>
        </div>

        <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4">
          <p className="font-medium text-white">환경 변수</p>
          <p className="mt-2">
            프론트엔드는 `VITE_API_BASE_URL`, 백엔드는 `APP_DATABASE_URL`,
            `APP_DB_PATH`, `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`,
            `CHROMA_PERSIST_DIRECTORY`, `CHROMA_COLLECTION_NAME`,
            `STT_PROVIDER_NAME`, `STT_PROVIDER_API_KEY`,
            `TTS_PROVIDER_NAME`, `TTS_PROVIDER_API_KEY`, `CALL_PROVIDER_NAME`,
            `CALL_PROVIDER_API_KEY`, `OUTBOUND_CALL_FROM_NUMBER`,
            `FRONTEND_ORIGINS`를 사용합니다.
          </p>
        </div>

        <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4">
          <p className="font-medium text-white">현재 동작 방식</p>
          <p className="mt-2">
            API 키 없이도 기본 플로우는 실행됩니다. 현재는 불만 접수, 상담 스크립트
            생성, 전사 적재, 규칙 기반 분류 JSON 생성 중심으로 동작하며, 실 STT/TTS
            연동 전에는 `mock` 결과를 반환합니다.
          </p>
        </div>
      </div>
    </section>
  );
}
