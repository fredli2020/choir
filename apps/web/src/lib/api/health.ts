import { apiFetch, ApiClientError } from "@/lib/api/client";
import type { HealthResponse } from "@/types/api";

export async function getHealthSummary() {
  try {
    const response = await apiFetch<HealthResponse>("/api/health/ready");
    return {
      label: response.status === "ok" ? "API reachable" : "API reported an error",
      detail: response.database
        ? "Readiness check passed, including database connectivity."
        : "Readiness endpoint responded, but the database is unavailable.",
    };
  } catch (error) {
    const message =
      error instanceof ApiClientError ? error.message : "Unable to reach the backend API.";

    return {
      label: "API unavailable",
      detail: message,
    };
  }
}
