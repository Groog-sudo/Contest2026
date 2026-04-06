import { useState } from 'react';
import { ApiRequestError, queryChat } from '../../lib/api.js';

const INITIAL_PROMPT =
  '예시 질문: "이번 주 과제 제출 규칙을 요약해줘" 또는 "강의 자료에서 REST API 핵심 개념을 설명해줘"';

export default function ChatPanel() {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError(null);
    setAnswer(null);

    if (!question.trim()) {
      setError('질문을 입력해 주세요.');
      return;
    }

    setIsLoading(true);

    try {
      const response = await queryChat({ question: question.trim(), top_k: 3 });
      setAnswer(response);
    } catch (caughtError) {
      if (caughtError instanceof ApiRequestError) {
        setError(caughtError.message);
      } else {
        setError('질의 처리 중 예상치 못한 오류가 발생했습니다.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <section className="rounded-[28px] border border-white/10 bg-white/8 p-6 shadow-xl shadow-slate-950/20 backdrop-blur">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold text-white">질문 패널</h2>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            업로드한 교육 자료를 바탕으로 질의응답을 수행하는 영역입니다.
          </p>
        </div>
        <span className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs font-medium text-emerald-100">
          RAG Ready
        </span>
      </div>

      <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">
            질문 입력
          </span>
          <textarea
            className="min-h-36 w-full rounded-2xl border border-white/10 bg-slate-950/45 px-4 py-3 text-sm text-slate-100 outline-none transition focus:border-cyan-300/40 focus:ring-2 focus:ring-cyan-300/20"
            placeholder={INITIAL_PROMPT}
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          />
        </label>

        <div className="flex flex-wrap items-center gap-3">
          <button
            className="rounded-full bg-cyan-300 px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isLoading}
            type="submit"
          >
            {isLoading ? '응답 생성 중...' : '질문하기'}
          </button>
          <p className="text-sm text-slate-400">
            현재 기본값은 `top_k=3` 입니다.
          </p>
        </div>
      </form>

      <div className="mt-6 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5">
          <p className="text-sm font-semibold text-slate-100">응답</p>
          <div className="mt-3 min-h-28 text-sm leading-7 text-slate-300">
            {error ? (
              <p className="text-rose-200">{error}</p>
            ) : answer ? (
              <p>{answer.answer}</p>
            ) : (
              <p className="text-slate-400">
                아직 응답이 없습니다. 문서를 업로드하고 질문을 입력해 보세요.
              </p>
            )}
          </div>
        </div>

        <div className="rounded-3xl border border-white/10 bg-slate-950/35 p-5">
          <p className="text-sm font-semibold text-slate-100">출처</p>
          <div className="mt-3 space-y-3 text-sm text-slate-300">
            {answer && answer.sources.length > 0 ? (
              answer.sources.map((source) => (
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
                답변이 생성되면 관련 문서 출처가 이곳에 표시됩니다.
              </p>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
