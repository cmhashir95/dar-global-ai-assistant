const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

export const getLeads = () => request("/api/leads");
export const getLead = (sessionId) => request(`/api/leads/${sessionId}`);
export const getConsultants = () => request("/api/consultants");
