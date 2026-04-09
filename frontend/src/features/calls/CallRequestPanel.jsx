import { useEffect, useState } from 'react';
import { ApiRequestError, requestComplaintCall } from '../../lib/api.js';

const INITIAL_FORM = {
  leadId: '',
  customerName: '',
  phoneNumber: '',
  orderId: '',
  incidentSummary: '',
  requestedResolution: '',
};

export default function CallRequestPanel({ lead, onCallReady }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [isLoading, setIsLoading] = useState(false);
  const [callResult, setCallResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!lead) {
      return;
    }

    setForm((current) => ({
      ...current,
      leadId: lead.leadId,
      customerName: lead.customerName,
      phoneNumber: lead.phoneNumber,
      orderId: lead.orderId,
      incidentSummary: lead.incidentSummary,
    }));
  }, [lead]);

  const updateField = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setCallResult(null);

    if (!form.leadId) {
      setError('먼저 불만 접수를 등록해 주세요.');
      return;
    }

    if (!form.incidentSummary.trim()) {
      setError('상담에서 다룰 핵심 불만 내용을 입력해 주세요.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await requestComplaintCall({
        lead_id: form.leadId,
        customer_name: form.customerName,
        phone_number: form.phoneNumber,
        order_id: form.orderId || null,
        incident_summary: form.incidentSummary.trim(),
        requested_resolution: form.requestedResolution.trim() || null,
        top_k: 3,
      });
      setCallResult(response);
      onCallReady?.({
        callId: response.call_id,
        incidentSummary: form.incidentSummary.trim(),
      });
    } catch (caughtError) {
      if (caughtError instanceof ApiRequestError) {
        setError(caughtError.message);
      } else {
        setError('상담 콜 요청 중 예상치 못한 오류가 발생했습니다.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="rounded-[28px] border border-white/10 bg-white/8 p-6 shadow-xl shadow-slate-950/20 backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-white">상담 콜 스크립트 생성</h2>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            접수된 고객 불만 정보를 기반으로 전화 상담용 스크립트와 근거 소스를 준비합니다.
          </p>
        </div>
        <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs font-medium text-emerald-100">
          Call Script
        </span>
      </div>

      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4 text-sm leading-6 text-slate-300">
            <p className="font-medium text-white">접수 고객</p>
            <p className="mt-2">{form.customerName || '접수 후 자동 표시'}</p>
            <p className="text-slate-400">{form.phoneNumber || '연락처 미등록'}</p>
          </div>
          <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4 text-sm leading-6 text-slate-300">
            <p className="font-medium text-white">주문 식별</p>
            <p className="mt-2">{form.orderId || '주문번호 미입력'}</p>
            <p className="text-slate-400">lead_id: {form.leadId || '생성 전'}</p>
          </div>
        </div>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">핵심 불만 내용</span>
          <textarea
            className="min-h-32 w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('incidentSummary', event.target.value)}
            placeholder='예시: "배달이 70분 지연되고 음식이 많이 식어서 도착했습니다."'
            value={form.incidentSummary}
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">원하는 조치 (선택)</span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('requestedResolution', event.target.value)}
            placeholder="예: refund / redelivery / recook"
            value={form.requestedResolution}
          />
        </label>

        <div className="flex flex-wrap items-center gap-3">
          <button
            className="rounded-full bg-cyan-300 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isLoading}
            type="submit"
          >
            {isLoading ? '스크립트 생성 중...' : '상담 콜 요청'}
          </button>
          <p className="text-sm text-slate-400">
            현재 기본 검색값은 `top_k=3`이며 문서 기반 상담 근거를 함께 조회합니다.
          </p>
        </div>
      </form>

      <div className="mt-6 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5">
          <p className="text-sm font-semibold text-slate-100">스크립트 미리보기</p>
          <div className="mt-3 min-h-28 text-sm leading-7 text-slate-300">
            {error ? (
              <p className="text-rose-200">{error}</p>
            ) : callResult ? (
              <div className="space-y-3">
                <p>{callResult.script_preview}</p>
                <p className="text-xs text-slate-400">
                  status: {callResult.status} | call_id: {callResult.call_id}
                </p>
                <p className="rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-sm text-slate-200">
                  {callResult.next_step}
                </p>
              </div>
            ) : (
              <p className="text-slate-400">
                아직 콜 요청 결과가 없습니다. 불만 접수 후 스크립트를 생성해 보세요.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5">
          <p className="text-sm font-semibold text-slate-100">상담 근거 소스</p>
          <div className="mt-3 space-y-3 text-sm text-slate-300">
            {callResult && callResult.sources.length > 0 ? (
              callResult.sources.map((source) => (
                <div className="rounded-2xl border border-white/8 bg-white/5 p-3" key={source.id}>
                  <p className="font-medium text-white">{source.title}</p>
                  <p className="mt-1 text-xs text-slate-400">
                    ID: {source.id}
                    {typeof source.score === 'number' ? ` | score: ${source.score.toFixed(2)}` : ''}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-slate-400">
                스크립트가 생성되면 접수 기록/지식베이스 근거가 이곳에 표시됩니다.
              </p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
