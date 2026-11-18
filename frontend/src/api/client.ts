import i18n, { currentLanguage } from "../i18n";
import type { TokenResponse } from "./types";

// The access token lives only in memory; the refresh token is an httpOnly cookie
// scoped to /api/auth that the browser sends automatically.
let accessToken: string | null = null;
let refreshInFlight: Promise<boolean> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

function detailToMessage(detail: unknown, fallback: string): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    // FastAPI validation errors: the form already checks the fields, so keep it short
    return i18n.t("errors.invalidData");
  }
  return fallback;
}

export async function refreshSession(): Promise<boolean> {
  // Several requests may 401 at once; share one refresh so the rotated cookie isn't reused.
  refreshInFlight ??= (async () => {
    try {
      const resp = await fetch("/api/auth/refresh", { method: "POST", credentials: "include" });
      if (!resp.ok) {
        setAccessToken(null);
        return false;
      }
      setAccessToken(((await resp.json()) as TokenResponse).access_token);
      return true;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

interface RequestOptions {
  method?: string;
  json?: unknown;
  form?: FormData;
  retry?: boolean;
}

export async function rawRequest(path: string, opts: RequestOptions = {}): Promise<Response> {
  // The API answers its messages (and Steam achievements) in the UI language
  const headers: Record<string, string> = { "Accept-Language": currentLanguage() };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (opts.json !== undefined) headers["Content-Type"] = "application/json";

  const resp = await fetch(path, {
    method: opts.method ?? (opts.json !== undefined || opts.form ? "POST" : "GET"),
    headers,
    body: opts.form ?? (opts.json !== undefined ? JSON.stringify(opts.json) : undefined),
    credentials: "include",
  });

  if (resp.status === 401 && opts.retry !== false && !path.startsWith("/api/auth/")) {
    if (await refreshSession()) return rawRequest(path, { ...opts, retry: false });
  }
  return resp;
}

export async function api<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const resp = await rawRequest(path, opts);
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}));
    throw new ApiError(resp.status, detailToMessage(body.detail, resp.statusText));
  }
  return (resp.status === 204 ? undefined : await resp.json()) as T;
}
