import { useEffect, useMemo, useState } from 'react';
import {
  ApiRequestError,
  fetchDashboardMetrics,
  fetchQueueTasks,
  processQueueTask,
  runQueueWorker,
} from '../../lib/api.js';

const PERIOD_OPTIONS = [7, 14, 30];

function percentage(value) {
  return `${(value * 100).toFixed(1)}%`;
}

function dayLabel(isoDate) {
  const [, month, day] = isoDate.split('-');
  return `${month}/${day}`;
}

function barHeight(value, maxValue) {
  if (maxValue <= 0) {
    return '4px';
  }
  const ratio = Math.max(0.08, value / maxValue);
  return `${Math.round(ratio * 100)}%`;
}

export default function MetricsPanel() {
  const [periodDays, setPeriodDays] = useState(7);
  const [metrics, setMetrics] = useState(null);
  const [queueItems, setQueueItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessingTaskId, setIsProcessingTaskId] = useState(null);
  const [isWorkerRunning, setIsWorkerRunning] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);
  const [error, setError] = useState(null);

  const load = async (selectedPeriod = periodDays) => {
    if (!metrics) {
      setIsLoading(true);
    }
    setError(null);

    try {
      const [metricsResponse, queueResponse] = await Promise.all([
        fetchDashboardMetrics(selectedPeriod),
        fetchQueueTasks(),
      ]);
      setMetrics(metricsResponse);
      setQueueItems(queueResponse.items.slice(0, 6));
    } catch (caughtError) {
      if (caughtError instanceof ApiRequestError) {
        setError(caughtError.message);
      } else {
        setError('대시보드 지표를 불러오는 중 오류가 발생했습니다.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const maxSeriesValue = useMemo(() => {
    if (!metrics?.series?.length) {
      return 0;
    }
    return Math.max(
      ...metrics.series.flatMap((point) => [point.leads, point.calls, point.assessments]),
    );
  }, [metrics]);

  const handleProcessTask = async (taskId) => {
    setActionMessage(null);
    setError(null);
    setIsProcessingTaskId(taskId);

    try {
      const response = await processQueueTask(taskId);
      if (response.status === 'done') {
        setActionMessage(`큐 작업 처리 완료: ${taskId}`);
      } else if (response.retry_queued) {
        setActionMessage(`큐 작업 재시도 대기열로 이동: ${taskId}`);
      } else {
        setActionMessage(`큐 작업 처리 실패: ${response.error_message ?? '원인을 확인해 주세요.'}`);
      }
    } catch (caughtError) {
      if (caughtError instanceof ApiRequestError) {
        setError(caughtError.message);
      } else {
        setError('큐 작업 처리 중 오류가 발생했습니다.');
      }
    } finally {
      setIsProcessingTaskId(null);
      await load();
    }
  };

  const handleRunWorker = async () => {
    setActionMessage(null);
    setError(null);
    setIsWorkerRunning(true);

    try {
      const response = await runQueueWorker(5);
      setActionMessage(
        `워커 실행 완료: processed ${response.processed}, done ${response.succeeded}, requeued ${response.requeued}, failed ${response.failed}`,
      );
    } catch (caughtError) {
      if (caughtError instanceof ApiRequestError) {
        setError(caughtError.message);
      } else {
        setError('큐 워커 실행 중 오류가 발생했습니다.');
      }
    } finally {
      setIsWorkerRunning(false);
      await load();
    }
  };

  useEffect(() => {
    void load(periodDays);
  }, [periodDays]);

  return (
    <section className="rounded-[28px] border border-white/10 bg-white/8 p-6 shadow-xl shadow-slate-950/20 backdrop-blur">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-xl font-semibold text-white">상담 성과 대시보드</h2>
        <div className="flex items-center gap-2">
          {PERIOD_OPTIONS.map((option) => (
            <button
              className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                periodDays === option
                  ? 'border-cyan-300/40 bg-cyan-300/20 text-cyan-100'
                  : 'border-white/10 bg-white/10 text-white hover:bg-white/20'
              }`}
              key={option}
              onClick={() => setPeriodDays(option)}
              type="button"
            >
              {option}일
            </button>
          ))}
          <button
            className="rounded-full border border-white/10 bg-white/10 px-4 py-2 text-xs font-semibold text-white transition hover:bg-white/20"
            onClick={() => void load()}
            type="button"
          >
            새로고침
          </button>
        </div>
      </div>

      <div className="mt-4">
        {error ? (
          <p className="rounded-2xl border border-rose-300/20 bg-rose-300/10 p-4 text-sm text-rose-100">
            {error}
          </p>
        ) : actionMessage ? (
          <p className="rounded-2xl border border-emerald-300/20 bg-emerald-300/10 p-4 text-sm text-emerald-100">
            {actionMessage}
          </p>
        ) : isLoading ? (
          <p className="text-sm text-slate-300">대시보드 데이터를 불러오는 중입니다...</p>
        ) : metrics ? (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4">
                <p className="text-xs text-slate-400">총 리드</p>
                <p className="mt-1 text-2xl font-semibold text-white">{metrics.total_leads}</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4">
                <p className="text-xs text-slate-400">통화 전환 리드</p>
                <p className="mt-1 text-2xl font-semibold text-white">{metrics.leads_with_calls}</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4">
                <p className="text-xs text-slate-400">전환율</p>
                <p className="mt-1 text-2xl font-semibold text-cyan-200">
                  {percentage(metrics.conversion_rate)}
                </p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4">
                <p className="text-xs text-slate-400">평가 완료 리드</p>
                <p className="mt-1 text-2xl font-semibold text-white">
                  {metrics.leads_with_assessments}
                </p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4">
                <p className="text-xs text-slate-400">완주율</p>
                <p className="mt-1 text-2xl font-semibold text-emerald-200">
                  {percentage(metrics.completion_rate)}
                </p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4">
                <p className="text-xs text-slate-400">평균 레벨 점수</p>
                <p className="mt-1 text-2xl font-semibold text-amber-200">
                  {metrics.avg_assessment_score.toFixed(1)}
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-medium text-white">{metrics.period_days}일 추이</p>
                <div className="flex items-center gap-2 text-[11px]">
                  <span className="inline-flex items-center gap-1 text-slate-300">
                    <span className="h-2.5 w-2.5 rounded-full bg-cyan-300/80" />
                    leads
                  </span>
                  <span className="inline-flex items-center gap-1 text-slate-300">
                    <span className="h-2.5 w-2.5 rounded-full bg-indigo-300/80" />
                    calls
                  </span>
                  <span className="inline-flex items-center gap-1 text-slate-300">
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-300/80" />
                    assessments
                  </span>
                </div>
              </div>
              <div className="mt-4 overflow-x-auto">
                <div className="inline-flex min-w-full items-end gap-3 pb-2">
                  {metrics.series.map((point) => (
                    <div className="flex min-w-[38px] flex-col items-center" key={point.date}>
                      <div className="flex h-28 items-end gap-1 rounded-xl border border-white/8 bg-white/5 px-2 py-2">
                        <span
                          className="w-1.5 rounded bg-cyan-300/80"
                          style={{ height: barHeight(point.leads, maxSeriesValue) }}
                          title={`leads ${point.leads}`}
                        />
                        <span
                          className="w-1.5 rounded bg-indigo-300/80"
                          style={{ height: barHeight(point.calls, maxSeriesValue) }}
                          title={`calls ${point.calls}`}
                        />
                        <span
                          className="w-1.5 rounded bg-emerald-300/80"
                          style={{ height: barHeight(point.assessments, maxSeriesValue) }}
                          title={`assessments ${point.assessments}`}
                        />
                      </div>
                      <p className="mt-2 text-[11px] text-slate-400">{dayLabel(point.date)}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-white">큐 상태</p>
                  <p className="mt-1 text-xs text-slate-400">
                    queued {metrics.queued_tasks} / processing {metrics.processing_tasks} / failed{' '}
                    {metrics.failed_tasks}
                  </p>
                </div>
                <button
                  className="rounded-full border border-emerald-300/30 bg-emerald-300/10 px-4 py-1.5 text-xs font-semibold text-emerald-100 transition hover:bg-emerald-300/20 disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={isWorkerRunning}
                  onClick={() => void handleRunWorker()}
                  type="button"
                >
                  {isWorkerRunning ? '워커 실행 중...' : '워커 5건 실행'}
                </button>
              </div>

              <div className="mt-3 space-y-2 text-xs text-slate-300">
                {queueItems.length > 0 ? (
                  queueItems.map((item) => (
                    <div
                      className="flex items-center justify-between gap-3 rounded-xl border border-white/8 bg-white/5 px-3 py-2"
                      key={item.task_id}
                    >
                      <div>
                        <p className="font-medium text-slate-100">
                          {item.task_type} · {item.status}
                        </p>
                        <p className="text-[11px] text-slate-400">
                          task_id: {item.task_id.slice(0, 8)}... · attempts {item.attempts}
                        </p>
                      </div>
                      <button
                        className="rounded-full border border-cyan-300/30 bg-cyan-300/10 px-3 py-1 text-[11px] font-semibold text-cyan-100 transition hover:bg-cyan-300/20 disabled:cursor-not-allowed disabled:opacity-50"
                        disabled={item.status !== 'queued' || isProcessingTaskId === item.task_id}
                        onClick={() => void handleProcessTask(item.task_id)}
                        type="button"
                      >
                        {isProcessingTaskId === item.task_id ? '처리 중...' : '단건 처리'}
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="text-slate-400">표시할 작업이 없습니다.</p>
                )}
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}
