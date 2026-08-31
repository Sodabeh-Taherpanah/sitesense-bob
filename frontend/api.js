// api.js
// Thin fetch wrappers for all backend endpoints.
// Centralising calls here means the rest of the frontend never hard-codes URLs.

const BASE_URL = "http://localhost:8000";

async function fetchJSON(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

const api = {
  getZones:   () => fetchJSON("/zones"),
  getAlerts:  () => fetchJSON("/alerts"),
  getHistory: (zoneId) => fetchJSON(`/zones/${encodeURIComponent(zoneId)}/history`),
};
