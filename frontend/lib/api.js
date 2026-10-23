/**
 * API Client for NotebookLM Python Backend
 * 
 * All AI/RAG processing is handled by the Python backend.
 * This client provides functions to interact with the backend API.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── Token Management ──────────────────────────────────────────────────────────

const TOKEN_KEY = 'notebooklm_access_token';

export function getStoredToken() {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token) {
  if (typeof window === 'undefined') return;
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

// ── Helper ────────────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const token = getStoredToken();

  const response = await fetch(url, {
    ...options,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `API Error: ${response.status}`);
  }

  return response;
}

// ── Authentication ────────────────────────────────────────────────────────────

export async function apiRegister(email, password, fullName = '') {
  const res = await apiFetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  return res.json();
}

export async function apiLogin(email, password) {
  const res = await apiFetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return res.json();
}

export async function apiGoogleAuth(idToken) {
  const res = await apiFetch('/api/auth/google', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id_token: idToken }),
  });
  return res.json();
}

export async function apiGetMe() {
  const res = await apiFetch('/api/auth/me');
  return res.json();
}

// ── Notebooks ────────────────────────────────────────────────────────────────

export async function createNotebook(title = 'Untitled Notebook', description = '') {
  const res = await apiFetch('/api/notebooks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, description }),
  });
  return res.json();
}

export async function getNotebooks() {
  const res = await apiFetch('/api/notebooks');
  return res.json();
}

export async function getNotebook(notebookId) {
  const res = await apiFetch(`/api/notebooks/${notebookId}`);
  return res.json();
}

export async function updateNotebook(notebookId, data) {
  const res = await apiFetch(`/api/notebooks/${notebookId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}

export async function deleteNotebook(notebookId) {
  const res = await apiFetch(`/api/notebooks/${notebookId}`, {
    method: 'DELETE',
  });
  return res.json();
}

// ── Sources (Documents) ──────────────────────────────────────────────────────

export async function uploadDocument(notebookId, file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await apiFetch(`/api/notebooks/${notebookId}/sources/upload`, {
    method: 'POST',
    body: formData,
  });
  return res.json();
}

export async function addUrl(notebookId, url) {
  const res = await apiFetch(`/api/notebooks/${notebookId}/sources/url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  return res.json();
}

export async function getDocuments(notebookId) {
  const res = await apiFetch(`/api/notebooks/${notebookId}/sources`);
  return res.json();
}

export async function deleteDocument(notebookId, sourceId) {
  const res = await apiFetch(`/api/notebooks/${notebookId}/sources/${sourceId}`, {
    method: 'DELETE',
  });
  return res.json();
}

export async function deleteAllDocuments(notebookId) {
  const res = await apiFetch(`/api/notebooks/${notebookId}/sources`, {
    method: 'DELETE',
  });
  return res.json();
}

/**
 * Get the URL to preview/download the original source file.
 * @param {string} notebookId
 * @param {string} sourceId
 * @returns {string} The URL to fetch the file (includes auth token as query param)
 */
export function getSourceFileUrl(notebookId, sourceId) {
  const token = getStoredToken();
  const base = `${API_BASE}/api/notebooks/${notebookId}/sources/${sourceId}/file`;
  return token ? `${base}?token=${encodeURIComponent(token)}` : base;
}

// ── Chat ──────────────────────────────────────────────────────────────────────

/**
 * Send a chat message with streaming response.
 * @param {string} notebookId 
 * @param {string} message 
 * @param {function} onContent - Callback for each content chunk
 * @param {function} onSources - Callback when sources are received
 * @param {function} onDone - Callback when streaming is complete
 */
export async function sendChatMessage(notebookId, message, { onContent, onSources, onDone }) {
  const url = `${API_BASE}/api/notebooks/${notebookId}/chat`;
  const token = getStoredToken();
  
  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Chat Error: ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          
          if (data.type === 'content' && onContent) {
            onContent(data.content);
          } else if (data.type === 'sources' && onSources) {
            onSources(data.sources);
          } else if (data.type === 'done' && onDone) {
            onDone(data.full_response);
          }
        } catch (e) {
          // Skip invalid JSON
        }
      }
    }
  }
}

// ── Chat History ─────────────────────────────────────────────────────────────

export async function getChatHistory(notebookId) {
  const res = await apiFetch(`/api/notebooks/${notebookId}/chat/history`);
  return res.json();
}

export async function clearChatHistory(notebookId) {
  const res = await apiFetch(`/api/notebooks/${notebookId}/chat/history`, {
    method: 'DELETE',
  });
  return res.json();
}

// ── Knowledge Graph ──────────────────────────────────────────────────────────

export async function getNotebookGraph(notebookId) {
  const res = await apiFetch(`/api/notebooks/${notebookId}/graph`);
  return res.json();
}
