import "server-only";

export function isClerkConfigured() {
  return Boolean(
    process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.trim() && process.env.CLERK_SECRET_KEY?.trim(),
  );
}

export function getClerkJwtTemplate() {
  const value = process.env.CLERK_JWT_TEMPLATE?.trim();
  return value ? value : null;
}
