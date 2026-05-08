/**
 * FNOL API Client
 * All communication with the FastAPI backend goes through here.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class APIError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function handleResponse(res) {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {}
    throw new APIError(`Request failed: ${detail}`, res.status, detail);
  }
  return res.json();
}

/** Upload a single FNOL PDF and return the full ClaimProcessingResponse */
export async function processClaim(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  // Use XHR for upload progress tracking
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${BASE_URL}/api/v1/claims/process`);

    if (onProgress) {
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100));
      };
    }

    xhr.onload = () => {
      try {
        const data = JSON.parse(xhr.responseText);
        if (xhr.status >= 200 && xhr.status < 300) resolve(data);
        else reject(new APIError(data.detail || 'Request failed', xhr.status, data.detail));
      } catch {
        reject(new APIError('Failed to parse response', xhr.status));
      }
    };

    xhr.onerror = () => reject(new APIError('Network error', 0));
    xhr.send(formData);
  });
}

/** Upload multiple FNOL PDFs (batch) */
export async function processClaimsBatch(files) {
  const formData = new FormData();
  for (const file of files) formData.append('files', file);

  const res = await fetch(`${BASE_URL}/api/v1/claims/batch`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(res);
}

/** Liveness check */
export async function checkHealth() {
  const res = await fetch(`${BASE_URL}/api/v1/health`, { cache: 'no-store' });
  return handleResponse(res);
}

/** Readiness check — includes Ollama status */
export async function checkReadiness() {
  const res = await fetch(`${BASE_URL}/api/v1/health/ready`, { cache: 'no-store' });
  try {
    return await res.json();
  } catch {
    return { status: 'degraded', ollama: { ok: false, detail: 'Unreachable' } };
  }
}

/** Get supported routing categories */
export async function getSupportedRoutes() {
  const res = await fetch(`${BASE_URL}/api/v1/claims/supported-routes`);
  return handleResponse(res);
}

export { BASE_URL, APIError };