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
            프론트엔드는 `VITE_API_BASE_URL`, 백엔드는 `APP_DB_PATH`,
            `OPENAI_API_KEY`, `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`,
            `PINECONE_NAMESPACE`, `STT_PROVIDER_NAME`, `STT_PROVIDER_API_KEY`,
            `TTS_PROVIDER_NAME`, `TTS_PROVIDER_API_KEY`, `CALL_PROVIDER_NAME`,
            `CALL_PROVIDER_API_KEY`, `OUTBOUND_CALL_FROM_NUMBER`,
            `FRONTEND_ORIGIN`을 사용합니다.
          </p>
        </div>

        <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4">
          <p className="font-medium text-white">현재 동작 방식</p>
          <p className="mt-2">
            API 키 없이도 앱은 실행됩니다. 다만 현재는 상담 리드 접수와 콜
            스크립트 초안 생성, 전사 적재, 레벨 추천 중심으로 동작하며, 실 STT/TTS
            및 통신 연동 전에는 `mock` 결과를 반환합니다.
          </p>
        </div>
      </div>
    </section>
  );
}
