import { publicEnv } from "@/lib/env";

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseJsonSafe(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return text;
  }
}

export async function apiPostJson<T>(path: string, body: unknown): Promise<T> {
  const url = `${publicEnv.apiBaseUrl}${path.startsWith("/") ? path : `/${path}`}`;
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!response.ok) {
    const parsed = await parseJsonSafe(response);
    const message =
      typeof parsed === "object" && parsed !== null && "detail" in parsed
        ? String((parsed as { detail?: unknown }).detail)
        : `Request failed (${response.status})`;
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export async function apiPatchJson<T>(path: string, body: unknown): Promise<T> {
  const url = `${publicEnv.apiBaseUrl}${path.startsWith("/") ? path : `/${path}`}`;
  const response = await fetch(url, {
    method: "PATCH",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!response.ok) {
    const parsed = await parseJsonSafe(response);
    const message =
      typeof parsed === "object" && parsed !== null && "detail" in parsed
        ? String((parsed as { detail?: unknown }).detail)
        : `Request failed (${response.status})`;
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export async function apiPostForm<T>(path: string, form: FormData): Promise<T> {
  const url = `${publicEnv.apiBaseUrl}${path.startsWith("/") ? path : `/${path}`}`;
  const response = await fetch(url, {
    method: "POST",
    body: form,
    cache: "no-store",
  });

  if (!response.ok) {
    const parsed = await parseJsonSafe(response);
    const message =
      typeof parsed === "object" && parsed !== null && "detail" in parsed
        ? String((parsed as { detail?: unknown }).detail)
        : `Request failed (${response.status})`;
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}

export async function apiGetJson<T>(path: string): Promise<T> {
  const url = `${publicEnv.apiBaseUrl}${path.startsWith("/") ? path : `/${path}`}`;
  const response = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await parseJsonSafe(response);
    const message =
      typeof body === "object" && body !== null && "detail" in body
        ? String((body as { detail?: unknown }).detail)
        : `Request failed (${response.status})`;
    throw new ApiError(message, response.status);
  }

  return (await response.json()) as T;
}
