/**
 * Central Typed API Client for FastAPI Backend.
 * Handles bearer token injection, automated error transformation, and network resilience.
 */

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API Error ${status}: ${detail}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/+$/, "") ||
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/+$/, "") ||
  "http://127.0.0.1:8000";

let authToken: string | null = null;
let onUnauthorizedCallback: (() => void) | null = null;

export function setApiAuthToken(token: string | null) {
  authToken = token;
}

export function setOnUnauthorized(cb: () => void) {
  onUnauthorizedCallback = cb;
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined | null>;
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { params, headers: customHeaders, ...rest } = options;

  let url = `${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== "") {
        searchParams.append(key, String(val));
      }
    });
    const queryString = searchParams.toString();
    if (queryString) {
      url += (url.includes("?") ? "&" : "?") + queryString;
    }
  }

  const headers = new Headers(customHeaders || {});

  // Do not set Content-Type if payload is FormData (browser will set boundary automatically)
  if (!(rest.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }

  let res: Response;
  try {
    res = await fetch(url, {
      ...rest,
      headers,
    });
  } catch (networkError: any) {
    const msg = networkError?.message
      ? `Failed to connect to backend server: ${networkError.message}`
      : "Failed to connect to backend server.";
    throw new ApiError(0, msg);
  }

  if (res.status === 401) {
    if (onUnauthorizedCallback) {
      onUnauthorizedCallback();
    }
    let detail = "Session expired or unauthorized.";
    try {
      const errJson = await res.json();
      detail = errJson?.detail || detail;
    } catch {}
    throw new ApiError(401, detail);
  }

  if (res.status === 204) {
    return {} as T;
  }

  if (!res.ok) {
    let detail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (typeof errJson?.detail === "string") {
        detail = errJson.detail;
      } else if (Array.isArray(errJson?.detail)) {
        detail = errJson.detail.map((d: any) => d.msg || JSON.stringify(d)).join("; ");
      } else if (errJson?.message) {
        detail = errJson.message;
      }
    } catch {
      detail = await res.text().catch(() => detail);
    }
    throw new ApiError(res.status, detail);
  }

  try {
    return (await res.json()) as T;
  } catch {
    return {} as T;
  }
}
