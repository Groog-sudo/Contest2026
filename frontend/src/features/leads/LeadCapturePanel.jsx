import { useState } from 'react';
import { ApiRequestError, registerLead } from '../../lib/api.js';

const INITIAL_FORM = {
  studentName: '',
  phoneNumber: '',
  courseInterest: '',
  learningGoal: '',
  preferredCallTime: '',
  consentToCall: true,
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
      const response = await registerLead({
        student_name: form.studentName,
        phone_number: form.phoneNumber,
        course_interest: form.courseInterest,
        learning_goal: form.learningGoal,
        preferred_call_time: form.preferredCallTime || null,
        consent_to_call: form.consentToCall,
      });

      const capturedLead = {
        leadId: response.lead_id,
        studentName: form.studentName.trim(),
        phoneNumber: form.phoneNumber.trim(),
        courseInterest: form.courseInterest.trim(),
      };

      setResult(response);
      onLeadCaptured?.(capturedLead);
    } catch (caughtError) {
      if (caughtError instanceof ApiRequestError) {
        setError(caughtError.message);
      } else {
        setError('상담 신청 접수 중 오류가 발생했습니다.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="rounded-[28px] border border-white/10 bg-white/8 p-6 shadow-xl shadow-slate-950/20 backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-white">상담 신청 접수</h2>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            수강생 연락처와 관심 과정을 먼저 받아 콜 파이프라인의 출발점을
            만듭니다.
          </p>
        </div>
        <span className="rounded-full border border-amber-300/20 bg-amber-300/10 px-3 py-1 text-xs font-medium text-amber-100">
          Lead Capture
        </span>
      </div>

      <form className="mt-6 grid gap-4 md:grid-cols-2" onSubmit={handleSubmit}>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">
            수강생 이름
          </span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('studentName', event.target.value)}
            placeholder="예: 김수강"
            value={form.studentName}
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">
            연락처
          </span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('phoneNumber', event.target.value)}
            placeholder="010-1234-5678"
            value={form.phoneNumber}
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">
            관심 과정
          </span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('courseInterest', event.target.value)}
            placeholder="예: AI 취업 부트캠프"
            value={form.courseInterest}
          />
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">
            희망 통화 시간
          </span>
          <input
            className="w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('preferredCallTime', event.target.value)}
            placeholder="예: 평일 오후 7시 이후"
            value={form.preferredCallTime}
          />
        </label>

        <label className="block md:col-span-2">
          <span className="mb-2 block text-sm font-medium text-slate-200">
            학습 목표
          </span>
          <textarea
            className="min-h-28 w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('learningGoal', event.target.value)}
            placeholder="예: 취업 포트폴리오를 만들고, 실무형 프로젝트 피드백을 받고 싶어요."
            value={form.learningGoal}
          />
        </label>

        <label className="flex items-center gap-3 rounded-2xl border border-white/8 bg-slate-950/30 px-4 py-3 text-sm text-slate-200 md:col-span-2">
          <input
            checked={form.consentToCall}
            className="h-4 w-4"
            onChange={(event) => updateField('consentToCall', event.target.checked)}
            type="checkbox"
          />
          AI 상담 전화 및 후속 연락에 동의합니다.
        </label>

        <div className="md:col-span-2 flex flex-wrap items-center gap-3">
          <button
            className="rounded-full bg-cyan-300 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? '접수 중...' : '상담 리드 등록'}
          </button>
          <p className="text-sm text-slate-400">
            등록 완료 후 바로 아래 패널에서 전화 멘토링 요청을 이어갈 수 있습니다.
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
          <p>
            현재는 상담 리드를 접수하고 콜 요청에 필요한 식별자를 생성하는
            단계까지 구현되어 있습니다.
          </p>
        )}
      </div>
    </section>
  );
}
