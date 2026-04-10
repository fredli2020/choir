function readApiBaseUrl() {
  const value = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

  if (value) {
    return value;
  }

  if (process.env.NODE_ENV !== "production") {
    return "http://127.0.0.1:8000";
  }

  throw new Error("NEXT_PUBLIC_API_BASE_URL must be set in production.");
}

export const appConfig = {
  apiBaseUrl: readApiBaseUrl(),
};
