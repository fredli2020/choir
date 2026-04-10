import "server-only";

import { cache } from "react";

import { getServerAuthState } from "@/lib/auth";
import {
  getCurrentUser,
  getCurrentUserContext,
  getCurrentUserOrganizations,
} from "@/lib/api/app";

export type AppBootstrapState =
  | { mode: "unconfigured" }
  | { mode: "signed-out" }
  | { mode: "missing-token" }
  | {
      mode: "ready";
      token: string;
      user: Awaited<ReturnType<typeof getCurrentUser>>;
      organizations: Awaited<ReturnType<typeof getCurrentUserOrganizations>>;
    };

export const getAppBootstrapState = cache(async (): Promise<AppBootstrapState> => {
  const authState = await getServerAuthState();

  if (!authState.clerkConfigured) {
    return { mode: "unconfigured" };
  }

  if (!authState.userId) {
    return { mode: "signed-out" };
  }

  if (!authState.token) {
    return { mode: "missing-token" };
  }

  const [user, organizations] = await Promise.all([
    getCurrentUser(authState.token),
    getCurrentUserOrganizations(authState.token),
  ]);

  return {
    mode: "ready",
    token: authState.token,
    user,
    organizations,
  };
});

export const getOrganizationAppData = cache(async (organizationId: string) => {
  const bootstrap = await getAppBootstrapState();

  if (bootstrap.mode !== "ready") {
    return bootstrap;
  }

  const context = await getCurrentUserContext(bootstrap.token, organizationId);

  return {
    ...bootstrap,
    context,
  };
});
