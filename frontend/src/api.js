const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

function readToken() {
  return localStorage.getItem("gradapp_access");
}

export async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...options.headers };
  const token = readToken();
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  const data = response.status === 204 ? null : await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data?.detail || data?.errors || "Something went wrong. Please try again.";
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

export function saveSession(data) {
  localStorage.setItem("gradapp_access", data.access);
  localStorage.setItem("gradapp_refresh", data.refresh);
  localStorage.setItem("gradapp_user", JSON.stringify(data.user));
}

export function clearSession() {
  localStorage.removeItem("gradapp_access");
  localStorage.removeItem("gradapp_refresh");
  localStorage.removeItem("gradapp_user");
}

export function getSavedUser() {
  try {
    return JSON.parse(localStorage.getItem("gradapp_user"));
  } catch {
    return null;
  }
}
