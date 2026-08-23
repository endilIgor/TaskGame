async function request<TResponse>(path: string, init?: RequestInit): Promise<TResponse> {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as TResponse;
  }

  return (await response.json()) as TResponse;
}

export async function apiGet<TResponse>(path: string): Promise<TResponse> {
  return request<TResponse>(path);
}

export async function apiGetOptional<TResponse>(path: string): Promise<TResponse | null> {
  const response = await fetch(`/api${path}`, { headers: { "Content-Type": "application/json" } });

  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return (await response.json()) as TResponse;
}

export async function apiPost<TResponse, TBody = unknown>(path: string, body?: TBody): Promise<TResponse> {
  return request<TResponse>(path, {
    method: "POST",
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export async function apiPatch<TResponse, TBody = unknown>(path: string, body: TBody): Promise<TResponse> {
  return request<TResponse>(path, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function apiDelete<TResponse = void>(path: string): Promise<TResponse> {
  return request<TResponse>(path, { method: "DELETE" });
}
