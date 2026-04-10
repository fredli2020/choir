import "server-only";

import { auth } from "@clerk/nextjs/server";

import { getClerkJwtTemplate, isClerkConfigured } from "@/lib/server-env";

export type ServerAuthState = {
  clerkConfigured: boolean;
  userId: string | null;
  token: string | null;
};

export async function getServerAuthState(): Promise<ServerAuthState> {
  if (!isClerkConfigured()) {
    return {
      clerkConfigured: false,
      userId: null,
      token: null,
    };
  }

  const authState = await auth();

  if (!authState.userId) {
    return {
      clerkConfigured: true,
      userId: null,
      token: null,
    };
  }

  const template = getClerkJwtTemplate();
  const token = template
    ? await authState.getToken({ template })
    : await authState.getToken();

  return {
    clerkConfigured: true,
    userId: authState.userId,
    token,
  };
}
