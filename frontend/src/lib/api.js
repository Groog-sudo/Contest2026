export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export class ApiRequestError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
  }
}

function normalizeErrorDetail(detail) {
  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === 'object' && 'msg' in item) {
          return item.msg;
        }
        return '입력값을 확인해 주세요.';
      })
      .join(' / ');
  }

  return '요청 처리에 실패했습니다.';
}

async function parseResponse(response) {
  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    const detail =
      payload && typeof payload === 'object' && 'detail' in payload
        ? payload.detail
        : '요청 처리에 실패했습니다.';
    throw new ApiRequestError(normalizeErrorDetail(detail), response.status);
  }

  return payload;
}

export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/api/v1/health`);
  return parseResponse(response);
}

export async function registerLead(payload) {
  const response = await fetch(`${API_BASE_URL}/api/v1/leads/register`, {
    body: JSON.stringify(payload),
    headers: {
      'Content-Type': 'application/json',
    },
    method: 'POST',
  });

  return parseResponse(response);
}

export async function requestComplaintCall(payload) {
  const response = await fetch(`${API_BASE_URL}/api/v1/calls/request`, {
    body: JSON.stringify(payload),
    headers: {
      'Content-Type': 'application/json',
    },
    method: 'POST',
  });

  return parseResponse(response);
}

export async function uploadCallRecording({ callId, leadId, file }) {
  const formData = new FormData();
  formData.append('call_id', callId);
  formData.append('lead_id', leadId);
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/v1/calls/recordings/upload`, {
    body: formData,
    method: 'POST',
  });

  return parseResponse(response);
}

export async function ingestCallTranscript(payload) {
  const response = await fetch(`${API_BASE_URL}/api/v1/calls/transcripts/ingest`, {
    body: JSON.stringify(payload),
    headers: {
      'Content-Type': 'application/json',
    },
    method: 'POST',
  });

  return parseResponse(response);
}

export async function previewCallTts(payload) {
  const response = await fetch(`${API_BASE_URL}/api/v1/calls/tts/preview`, {
    body: JSON.stringify(payload),
    headers: {
      'Content-Type': 'application/json',
    },
    method: 'POST',
  });

  return parseResponse(response);
}

export async function analyzeIncident(payload) {
  const response = await fetch(`${API_BASE_URL}/api/v1/analyses/analyze`, {
    body: JSON.stringify(payload),
    headers: {
      'Content-Type': 'application/json',
    },
    method: 'POST',
  });

  return parseResponse(response);
}

export async function fetchDashboardMetrics(periodDays = 7) {
  const query = new URLSearchParams({ period_days: String(periodDays) });
  const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/metrics?${query.toString()}`);
  return parseResponse(response);
}

export async function fetchQueueTasks() {
  const response = await fetch(`${API_BASE_URL}/api/v1/queue/tasks`);
  return parseResponse(response);
}

export async function processQueueTask(taskId) {
  const response = await fetch(`${API_BASE_URL}/api/v1/queue/process`, {
    body: JSON.stringify({ task_id: taskId }),
    headers: {
      'Content-Type': 'application/json',
    },
    method: 'POST',
  });
  return parseResponse(response);
}

export async function runQueueWorker(limit = 10) {
  const response = await fetch(`${API_BASE_URL}/api/v1/queue/workers/run`, {
    body: JSON.stringify({ limit }),
    headers: {
      'Content-Type': 'application/json',
    },
    method: 'POST',
  });
  return parseResponse(response);
}

export async function uploadKnowledgeDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/v1/documents/upload`, {
    body: formData,
    method: 'POST',
  });

  return parseResponse(response);
}
