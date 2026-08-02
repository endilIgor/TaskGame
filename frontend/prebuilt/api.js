const API_BASE = "/api";
async function request   (path        , options              = {})             {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    ...options,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }
  return response.json()              ;
}
export function apiGet   (path        )             {
  return request   (path);
}
export function apiPost   (path        , body          )             {
  return request   (path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
}
export function apiPatch   (path        , body         )             {
  return request   (path, { method: "PATCH", body: JSON.stringify(body) });
}
