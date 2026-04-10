import type { ReactNode } from "react";
import { redirect } from "next/navigation";

import { AppShell } from "@/components/app/app-shell";
import { SetupPanel } from "@/components/app/setup-panel";
import { getOrganizationAppData } from "@/lib/app-data";

type LayoutProps = {
  children: ReactNode;
  params: Promise<{ orgId: string }>;
};

export default async function OrganizationLayout({ children, params }: LayoutProps) {
  const { orgId } = await params;
  const state = await getOrganizationAppData(orgId);

  if (state.mode === "unconfigured") {
    return (
      <SetupPanel
        title="Add Clerk to unlock the app shell"
        description="This protected route expects Clerk-backed authentication before it can request organization context from Django."
        body="Set NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY and CLERK_SECRET_KEY in apps/web/.env.local. If Django verifies a custom audience claim, also set CLERK_JWT_TEMPLATE to the matching Clerk template name."
      />
    );
  }

  if (state.mode === "signed-out") {
    redirect("/sign-in");
  }

  if (state.mode === "missing-token") {
    return (
      <SetupPanel
        title="No backend token is available for this session"
        description="Clerk can see the user, but the frontend could not mint the token Django expects on protected API calls."
        body="If your backend expects a custom audience, create a Clerk JWT template and set CLERK_JWT_TEMPLATE in apps/web/.env.local so the API requests include the correct token."
      />
    );
  }

  if (!state.context.organization || !state.context.membership) {
    redirect("/app");
  }

  return (
    <AppShell currentUser={state.user} context={state.context} organizations={state.organizations}>
      {children}
    </AppShell>
  );
}
