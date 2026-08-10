// CRITICAL-003: API_BASE must be exported so Login.jsx, useProgressStream.js,
// and ProjectWorkspace.jsx can import it. Previously it was module-local (no
// export keyword), which caused all three consumers to receive `undefined`.
export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:5001';


export async function apiFetch(path, options = {}, token = null) {
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  return res;
}
