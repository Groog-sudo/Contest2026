import { useEffect, useState } from 'react';
import { analyzeIncident, ApiRequestError } from '../../lib/api.js';

const INITIAL_FORM = {
  leadId: '',
  callId: '',
  customerMessage: '',
  orderId: '',
  orderItems: '',
  evidenceAvailable: 'unknown',
  requestedResolution: '',
};

export default function IncidentAnalysisPanel({ lead, callContext }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!lead) {
      return;
    }
    setForm((current) => ({
      ...current,
      leadId: lead.leadId,
      customerMessage: lead.incidentSummary,
      orderId: lead.orderId,
    }));
  }, [lead]);

  useEffect(() => {
    if (!callContext) {
      return;
    }
    setForm((current) => ({
      ...current,
      callId: callContext.callId,
      customerMessage: callContext.incidentSummary || current.customerMessage,
    }));
  }, [callContext]);

  const updateField = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setResult(null);

    if (!form.leadId) {
      setError('먼저 불만 접수를 등록해 주세요.');
      return;
    }
    if (!form.customerMessage.trim()) {
      setError('분석할 고객 메시지를 입력해 주세요.');
      return;
    }

    setIsLoading(true);
    try {
      const requestedResolution = form.requestedResolution
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);
      const orderItems = form.orderItems
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);

      const response = await analyzeIncident({
        lead_id: form.leadId,
        call_id: form.callId || null,
        customer_message: form.customerMessage.trim(),
        order_id: form.orderId || null,
        order_items: orderItems,
        evidence_available: form.evidenceAvailable,
        requested_resolution: requestedResolution,
      });
      setResult(response);
    } catch (caughtError) {
      if (caughtError instanceof ApiRequestError) {
        setError(caughtError.message);
      } else {
        setError('이슈 분석 처리 중 오류가 발생했습니다.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="rounded-[28px] border border-white/10 bg-white/8 p-6 shadow-xl shadow-slate-950/20 backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-white">이슈 분류 JSON 생성</h2>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            고객 발화를 기반으로 카테고리/책임 주체/심각도/피드백 문안을 구조화합니다.
          </p>
        </div>
        <span className="rounded-full border border-fuchsia-300/20 bg-fuchsia-300/10 px-3 py-1 text-xs font-medium text-fuchsia-100">
          Incident Analysis
        </span>
      </div>

      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-200">lead_id</span>
            <input
              className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none"
              onChange={(event) => updateField('leadId', event.target.value)}
              value={form.leadId}
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-200">call_id (선택)</span>
            <input
              className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none"
              onChange={(event) => updateField('callId', event.target.value)}
              value={form.callId}
            />
          </label>
        </div>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">고객 메시지</span>
          <textarea
            className="min-h-28 w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none"
            onChange={(event) => updateField('customerMessage', event.target.value)}
            value={form.customerMessage}
          />
        </label>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-200">주문번호</span>
            <input
              className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none"
              onChange={(event) => updateField('orderId', event.target.value)}
              value={form.orderId}
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-200">증빙 상태</span>
            <select
              className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none"
              onChange={(event) => updateField('evidenceAvailable', event.target.value)}
              value={form.evidenceAvailable}
            >
              <option value="unknown">unknown</option>
              <option value="none">none</option>
              <option value="photo">photo</option>
              <option value="video">video</option>
            </select>
          </label>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-200">주문메뉴 (쉼표 구분)</span>
            <input
              className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none"
              onChange={(event) => updateField('orderItems', event.target.value)}
              value={form.orderItems}
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-slate-200">요청 조치 (쉼표 구분)</span>
            <input
              className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none"
              onChange={(event) => updateField('requestedResolution', event.target.value)}
              placeholder="refund, redelivery"
              value={form.requestedResolution}
            />
          </label>
        </div>

        <button
          className="rounded-full bg-cyan-300 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isLoading}
          type="submit"
        >
          {isLoading ? '분석 중...' : '이슈 분석 실행'}
        </button>
      </form>

      <div className="mt-5 rounded-3xl border border-white/10 bg-slate-950/35 p-5 text-sm leading-6 text-slate-300">
        {error ? (
          <p className="text-rose-200">{error}</p>
        ) : result ? (
          <pre className="overflow-auto whitespace-pre-wrap text-xs leading-6 text-slate-200">
            {JSON.stringify(result, null, 2)}
          </pre>
        ) : (
          <p>분석 결과 JSON은 여기 표시됩니다.</p>
        )}
      </div>
    </section>
  );
}
