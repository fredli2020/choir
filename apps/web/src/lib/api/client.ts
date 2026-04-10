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
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) {
        detail = payload.detail;
      }
    } catch {
      // Keep the fallback message when the response is not JSON.
    }

    throw new ApiClientError(detail, response.status);
  }

  return (await response.json()) as T;
}
