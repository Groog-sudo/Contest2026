export default function AppShell({ children, latestLead }) {
  return (
    <main className="min-h-screen px-4 py-8 text-slate-100 sm:px-6 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 overflow-hidden rounded-[28px] border border-white/10 bg-white/6 p-8 shadow-2xl shadow-slate-950/30 backdrop-blur">
          <div className="mb-4 inline-flex rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.28em] text-cyan-100">
            AI Mentoring Call Flow
          </div>
          <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
            <div>
              <h1 className="max-w-3xl text-3xl font-semibold leading-tight text-white sm:text-4xl">
                수강생 연락처를 받고 RAG 기반 전화 멘토링으로 이어지는 상담 스타터
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
                수강생이 남긴 연락처와 관심 과정을 바탕으로 상담 정보를 접수하고,
                지식베이스에서 근거를 찾은 뒤 AI 멘토링 콜 스크립트를 준비하는
                공모전용 기본 템플릿입니다.
              </p>
            </div>

            <div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5 text-sm text-slate-300">
              <p className="font-medium text-white">운영 포인트</p>
              <p className="mt-2 leading-6">
                상담 신청 접수, 콜 스크립트 생성, 지식베이스 업로드, 설정 안내를
                한 화면에서 확인할 수 있습니다.
              </p>
              <p className="mt-4 rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-xs leading-5 text-slate-200">
                {latestLead
                  ? `최근 접수: ${latestLead.studentName} / ${latestLead.courseInterest}`
                  : '최근 접수된 리드가 아직 없습니다. 상담 신청을 먼저 등록해 보세요.'}
              </p>
            </div>
          </div>
        </header>

        {children}
      </div>
    </main>
  );
}
