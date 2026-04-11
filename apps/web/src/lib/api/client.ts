import { appConfig } from "@/lib/config";

type Primitive = string | number | boolean;
type SearchValue = Primitive | null | undefined;

export class ApiClientError extends Error {
  readonly status: number;

  constructor(message: string, status = 500) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
  }
}

function extractErrorDetail(payload: unknown): string | null {
  if (payload == null) {
    return null;
  }

  if (typeof payload === "string") {
    return payload;
  }

  if (typeof payload !== "object") {
    return null;
  }

  const record = payload as Record<string, unknown>;
  const detail = record.detail;
  if (typeof detail === "string" && detail) {
    return detail;
  }

  for (const [key, value] of Object.entries(record)) {
    if (Array.isArray(value) && value.length > 0) {
      const first = value[0];
      if (typeof first === "string" && first) {
        return `${key}: ${first}`;
      }
    }
    if (typeof value === "string" && value) {
      return `${key}: ${value}`;
    }
  }

  return null;
}

function buildUrl(path: string, searchParams?: Record<string, SearchValue>) {
  const url = new URL(path, appConfig.apiBaseUrl);

  for (const [key, value] of Object.entries(searchParams ?? {})) {
    if (value === undefined || value === null || value === "") {
      continue;
    }

    url.searchParams.set(key, String(value));
  }

  return url.toString();
}

type ApiFetchOptions = RequestInit & {
  token?: string | null;
  searchParams?: Record<string, SearchValue>;
};

export async function apiFetch<T>(path: string, init?: ApiFetchOptions): Promise<T> {
  const url = buildUrl(path, init?.searchParams);
  const headers = new Headers(init?.headers);

  headers.set("Accept", "application/json");

  if (init?.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (init?.token) {
    headers.set("Authorization", `Bearer ${init.token}`);
  }

  const response = await fetch(url, {
    ...init,
    cache: "no-store",
    headers,
  });

  if (!response.ok) {
    let detail = `Request to ${url} failed with ${response.status}.`;

    try {
      const payload = (await response.json()) as unknown;
      const extracted = extractErrorDetail(payload);
      if (extracted) {
        detail = extracted;
      }
    } catch {
      // Keep the fallback message when the response is not JSON.
    }

    throw new ApiClientError(detail, response.status);
  }

  return (await response.json()) as T;
}
