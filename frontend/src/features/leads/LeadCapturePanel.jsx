import { useState } from 'react';
import { ApiRequestError, registerLead } from '../../lib/api.js';

const INITIAL_FORM = {
  customerName: '',
  phoneNumber: '',
  orderId: '',
  orderItems: '',
  incidentSummary: '',
  requestedResolution: '',
  preferredContactTime: '',
  consentToContact: true,
};

export default function LeadCapturePanel({ onLeadCaptured }) {
  const [form, setForm] = useState(INITIAL_FORM);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const updateField = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setResult(null);
    setIsSubmitting(true);

    try {
      const orderItems = form.orderItems
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean);

      const response = await registerLead({
        customer_name: form.customerName,
        phone_number: form.phoneNumber,
        order_id: form.orderId || null,
        order_items: orderItems,
        incident_summary: form.incidentSummary,
        requested_resolution: form.requestedResolution || null,
        preferred_contact_time: form.preferredContactTime || null,
        consent_to_contact: form.consentToContact,
      });

      const capturedLead = {
        leadId: response.lead_id,
        customerName: form.customerName.trim(),
        phoneNumber: form.phoneNumber.trim(),
        orderId: form.orderId.trim(),
        incidentSummary: form.incidentSummary.trim(),
      };

      setResult(response);
      onLeadCaptured?.(capturedLead);
    } catch (caughtError) {
      if (caughtError instanceof ApiRequestError) {
        setError(caughtError.message);
      } else {
        setError('불만 접수 처리 중 오류가 발생했습니다.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="rounded-[28px] border border-white/10 bg-white/8 p-6 shadow-xl shadow-slate-950/20 backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-white">배달 불만 접수</h2>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            고객 기본 정보와 이슈 요약을 먼저 접수해 상담/분류 플로우의 출발점을 만듭니다.
          </p>
        </div>
        <span className="rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1 text-xs font-medium text-amber-100">
          Complaint Intake
        </span>
      </div>

      <form className="mt-6 grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">고객명</span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('customerName', event.target.value)}
            placeholder="예: 홍고객"
            value={form.customerName}
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">연락처</span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('phoneNumber', event.target.value)}
            placeholder="010-1234-5678"
            value={form.phoneNumber}
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">주문번호 (선택)</span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('orderId', event.target.value)}
            placeholder="예: ORD-2026-001"
            value={form.orderId}
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">주문 메뉴 (쉼표 구분)</span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('orderItems', event.target.value)}
            placeholder="예: 치킨, 콜라"
            value={form.orderItems}
          />
        </label>

        <label className="block md:col-span-2">
          <span className="mb-2 block text-sm font-medium text-slate-200">핵심 불만 요약</span>
          <textarea
            className="min-h-28 w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('incidentSummary', event.target.value)}
            placeholder="예: 배달이 1시간 이상 늦고 음식이 식었습니다."
            value={form.incidentSummary}
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">원하는 조치 (선택)</span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('requestedResolution', event.target.value)}
            placeholder="예: 환불"
            value={form.requestedResolution}
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">희망 연락 시간 (선택)</span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('preferredContactTime', event.target.value)}
            placeholder="예: 오늘 오후 8시 이후"
            value={form.preferredContactTime}
          />
        </label>

        <label className="flex items-center gap-3 rounded-2xl border border-white/8 bg-slate-950/30 px-4 py-3 text-sm text-slate-200 md:col-span-2">
          <input
            checked={form.consentToContact}
            className="h-4 w-4"
            onChange={(event) => updateField('consentToContact', event.target.checked)}
            type="checkbox"
          />
          상담 및 후속 연락에 동의합니다.
        </label>

        <div className="md:col-span-2 flex flex-wrap items-center gap-3">
          <button
            className="rounded-full bg-cyan-300 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? '접수 중...' : '불만 접수 등록'}
          </button>
          <p className="text-sm text-slate-400">
            접수 완료 후 바로 아래 패널에서 상담 콜 스크립트 생성을 진행할 수 있습니다.
          </p>
        </div>
      </form>

      <div className="mt-5 rounded-3xl border border-white/10 bg-slate-950/35 p-5 text-sm leading-6 text-slate-300">
        {error ? (
          <p className="text-rose-200">{error}</p>
        ) : result ? (
          <div className="space-y-2">
            <p className="font-semibold text-white">접수 완료</p>
            <p>{result.next_action}</p>
            <p className="text-xs text-slate-400">lead_id: {result.lead_id}</p>
          </div>
        ) : (
          <p>현재 단계에서는 고객 불만 접수와 상담 식별자 생성까지 자동화되어 있습니다.</p>
        )}
      </div>
    </section>
  );
}
