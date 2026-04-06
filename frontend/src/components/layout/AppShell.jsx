export default function AppShell({ children }) {
  return (
    <main className="min-h-screen px-4 py-8 text-slate-100 sm:px-6 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 overflow-hidden rounded-[28px] border border-white/10 bg-white/6 p-8 shadow-2xl shadow-slate-950/30 backdrop-blur">
          <div className="mb-4 inline-flex rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.28em] text-cyan-100">
            AI Education Solution
          </div>
          <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
            <div>
              <h1 className="max-w-3xl text-3xl font-semibold leading-tight text-white sm:text-4xl">
                교육 문서를 이해하고 바로 답하는 RAG 어시스턴트 스타터
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
                강의자료, 공지, 운영 문서를 업로드하고 질문을 던지면 학습자와
                운영자가 필요한 답을 더 빠르게 찾을 수 있도록 준비된 공모전용
                기본 템플릿입니다.
              </p>
            </div>

            <div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5 text-sm text-slate-300">
              <p className="font-medium text-white">핵심 화면</p>
              <p className="mt-2 leading-6">
                문서 업로드, 질의응답, 출처 확인, 설정 안내를 한 화면에서 바로
                확인할 수 있습니다.
              </p>
            </div>
          </div>
        </header>

        {children}
      </div>
    </main>
  );
}
