/**
 * Client for the LinkSnap Flask REST API (see /backend).
 * Configure the base URL with VITE_API_BASE_URL; defaults to a local Flask dev server.
 */
export const API_BASE_URL = (
  (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? "http://localhost:5000"
).replace(/\/$/, "");

export interface ShortLink {
  id: number;
  code: string;
  original_url: string;
  short_url: string;
  created_at: string;
  clicks: number;
}

export interface LinkList {
  total: number;
  urls: ShortLink[];
}

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(
      `Can't reach the LinkSnap server at ${API_BASE_URL}. Make sure the Flask API is running.`,
      0,
    );
  }

  if (!res.ok) {
    let message = `Request failed (${res.status}).`;
    try {
      const body = (await res.json()) as { error?: string };
      if (body.error) message = body.error;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(message, res.status);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  shorten: (url: string) =>
    request<ShortLink>("/api/shorten", { method: "POST", body: JSON.stringify({ url }) }),
  list: () => request<LinkList>("/api/urls"),
  remove: (code: string) =>
    request<void>(`/api/urls/${encodeURIComponent(code)}`, { method: "DELETE" }),
};
