import { appConfig } from "@/lib/config";

export class ApiClientError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ApiClientError";
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = new URL(path, appConfig.apiBaseUrl).toString();
  const response = await fetch(url, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new ApiClientError(`Request to ${url} failed with ${response.status}.`);
  }

  return (await response.json()) as T;
}
