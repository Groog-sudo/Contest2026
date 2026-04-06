import { useState } from 'react';
import { ApiRequestError, uploadKnowledgeDocument } from '../../lib/api.js';

export default function KnowledgeBasePanel() {
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleUpload = async (event) => {
    event.preventDefault();
    setMessage(null);
    setError(null);

    if (!file) {
      setError('업로드할 파일을 먼저 선택해 주세요.');
      return;
    }

    setIsUploading(true);

    try {
      const response = await uploadKnowledgeDocument(file);
      setMessage(
        response.status === 'accepted'
          ? `멘토링 지식 문서가 접수되었습니다. document_id=${response.document_id}`
          : '문서는 접수되었지만 아직 RAG 지식베이스 연결 전이라 실제 색인은 대기 상태입니다.',
      );
      setFile(null);
    } catch (caughtError) {
      if (caughtError instanceof ApiRequestError) {
        setError(caughtError.message);
      } else {
        setError('멘토링 자료 업로드 중 오류가 발생했습니다.');
      }
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <section className="rounded-[28px] border border-white/10 bg-white/8 p-6 shadow-xl shadow-slate-950/20 backdrop-blur">
      <h2 className="text-xl font-semibold text-white">멘토링 지식베이스 업로드</h2>
      <p className="mt-2 text-sm leading-6 text-slate-300">
        상담 스크립트가 참고할 커리큘럼, FAQ, 수강 후기, 운영 가이드를 업로드하는
        영역입니다.
      </p>

      <form className="mt-5 space-y-4" onSubmit={handleUpload}>
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-slate-200">
            파일 선택
          </span>
          <input
            className="block w-full rounded-2xl border border-dashed border-white/15 bg-slate-950/35 px-4 py-3 text-sm text-slate-300 file:mr-4 file:rounded-full file:border-0 file:bg-cyan-300 file:px-4 file:py-2 file:text-sm file:font-semibold file:text-slate-950 hover:file:bg-cyan-200"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            type="file"
          />
        </label>

        <button
          className="rounded-full border border-white/10 bg-white/10 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-white/15 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isUploading}
          type="submit"
        >
          {isUploading ? '업로드 중...' : '지식 문서 업로드'}
        </button>
      </form>

      <div className="mt-4 rounded-2xl border border-white/8 bg-slate-950/30 p-4 text-sm leading-6 text-slate-300">
        {error ? (
          <p className="text-rose-200">{error}</p>
        ) : message ? (
          <p>{message}</p>
        ) : (
          <p>
            상담 플레이북, 과정 소개서, 취업 사례집처럼 통화 품질을 높이는 자료를
            연결하는 확장 지점입니다.
          </p>
        )}
      </div>
    </section>
  );
}
