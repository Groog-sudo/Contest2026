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

export async function requestMentoringCall(payload) {
  const response = await fetch(`${API_BASE_URL}/api/v1/calls/request`, {
    body: JSON.stringify(payload),
    headers: {
      'Content-Type': 'application/json',
    },
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

export async function evaluateLevelTest(payload) {
  const response = await fetch(`${API_BASE_URL}/api/v1/assessments/level-test`, {
    body: JSON.stringify(payload),
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
