export default function AppShell({ children, latestLead }) {
  return (
    <main className="min-h-screen px-4 py-8 text-slate-100 sm:px-6 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <header className="mb-8 overflow-hidden rounded-[28px] border border-white/10 bg-white/6 p-8 shadow-2xl shadow-slate-950/30 backdrop-blur">
          <div className="mb-4 inline-flex rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.28em] text-cyan-100">
            Delivery Complaint AI Flow
          </div>
          <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
            <div>
              <h1 className="max-w-3xl text-3xl font-semibold leading-tight text-white sm:text-4xl">
                배달 주문 불만을 전화 상담으로 접수하고 자동 분류까지 연결하는 운영 스타터
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300 sm:text-base">
                고객 불만 접수, 상담 스크립트 생성, RAG 근거 조회, JSON 분류 결과 생성을
                한 화면에서 점검할 수 있도록 구성한 공모전용 기본 템플릿입니다.
              </p>
            </div>

            <div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5 text-sm text-slate-300">
              <p className="font-medium text-white">운영 포인트</p>
              <p className="mt-2 leading-6">
                불만 접수, 콜 스크립트, 이슈 분류 JSON, 지식 문서 업로드를
                단일 대시보드에서 확인할 수 있습니다.
              </p>
              <p className="mt-4 rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-xs leading-5 text-slate-200">
                {latestLead
                  ? `최근 접수: ${latestLead.customerName} / ${latestLead.orderId || '주문번호 미입력'}`
                  : '최근 접수 건이 없습니다. 먼저 불만 접수를 등록해 보세요.'}
              </p>
            </div>
          </div>
        </header>

        {children}
      </div>
    </main>
  );
}
