import { useEffect, useState } from 'react';
import { ApiRequestError, requestMentoringCall } from '../../lib/api.js';

const INITIAL_FORM = {
  leadId: '',
  studentName: '',
  phoneNumber: '',
  courseInterest: '',
  studentQuestion: '',
};

export default function CallRequestPanel({ lead }) {
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
      studentName: lead.studentName,
      phoneNumber: lead.phoneNumber,
      courseInterest: lead.courseInterest,
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
      setError('먼저 상담 리드를 등록해 주세요.');
      return;
    }

    if (!form.studentQuestion.trim()) {
      setError('전화에서 다룰 질문을 입력해 주세요.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await requestMentoringCall({
        lead_id: form.leadId,
        student_name: form.studentName,
        phone_number: form.phoneNumber,
        course_interest: form.courseInterest,
        student_question: form.studentQuestion.trim(),
        top_k: 3,
      });
      setCallResult(response);
    } catch (caughtError) {
      if (caughtError instanceof ApiRequestError) {
        setError(caughtError.message);
      } else {
        setError('멘토링 콜 요청 중 예상치 못한 오류가 발생했습니다.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="rounded-[28px] border border-white/10 bg-white/8 p-6 shadow-xl shadow-slate-950/20 backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-white">AI 멘토링 콜 요청</h2>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            접수된 수강생 정보를 바탕으로 통화용 멘토링 스크립트를 준비합니다.
          </p>
        </div>
        <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs font-medium text-emerald-100">
          Call Script
        </span>
      </div>

      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4 text-sm leading-6 text-slate-300">
            <p className="font-medium text-white">등록된 리드</p>
            <p className="mt-2">
              {form.studentName || '리드를 등록하면 이름이 표시됩니다.'}
            </p>
            <p className="text-slate-400">{form.phoneNumber || '연락처 미등록'}</p>
          </div>
          <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4 text-sm leading-6 text-slate-300">
            <p className="font-medium text-white">관심 과정</p>
            <p className="mt-2">
              {form.courseInterest || '리드를 등록하면 과정 정보가 표시됩니다.'}
            </p>
            <p className="text-slate-400">
              lead_id: {form.leadId || '생성 전'}
            </p>
          </div>
        </div>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">
            통화에서 다룰 핵심 질문
          </span>
          <textarea
            className="min-h-36 w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            onChange={(event) => updateField('studentQuestion', event.target.value)}
            placeholder='예시: "비전공자인데 3개월 안에 어떤 프로젝트를 준비하면 좋을까요?"'
            value={form.studentQuestion}
          />
        </label>

        <div className="flex flex-wrap items-center gap-3">
          <button
            className="rounded-full bg-cyan-300 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isLoading}
            type="submit"
          >
            {isLoading ? '스크립트 생성 중...' : '멘토링 콜 요청'}
          </button>
          <p className="text-sm text-slate-400">
            현재 기본값은 `top_k=3`이며, 자동 발신 전 단계까지 시연할 수 있습니다.
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
                아직 콜 요청 결과가 없습니다. 리드를 등록하고 질문을 입력해 보세요.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5">
          <p className="text-sm font-semibold text-slate-100">스크립트 근거</p>
          <div className="mt-3 space-y-3 text-sm text-slate-300">
            {callResult && callResult.sources.length > 0 ? (
              callResult.sources.map((source) => (
                <div
                  className="rounded-2xl border border-white/8 bg-white/5 p-3"
                  key={source.id}
                >
                  <p className="font-medium text-white">{source.title}</p>
                  <p className="mt-1 text-xs text-slate-400">
                    ID: {source.id}
                    {typeof source.score === 'number'
                      ? ` | score: ${source.score.toFixed(2)}`
                      : ''}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-slate-400">
                스크립트가 생성되면 상담 신청서 또는 지식베이스 근거가 이곳에 표시됩니다.
              </p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
