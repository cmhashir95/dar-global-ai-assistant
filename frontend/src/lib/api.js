const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json();
}

export function sendChatMessage(payload) {
  return request("/api/chat", { method: "POST", body: JSON.stringify(payload) });
}

export function bookSlot(payload) {
  return request("/api/consultants/book", { method: "POST", body: JSON.stringify(payload) });
}

export function getProperties() {
  return request("/api/properties");
}

export function getSessionId() {
  const key = "dar_global_session_id";
  let id = localStorage.getItem(key);
  if (!id) {
    id = `sess-${Math.random().toString(36).slice(2)}-${Date.now()}`;
    localStorage.setItem(key, id);
  }
  return id;
}
