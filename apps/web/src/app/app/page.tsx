import Link from "next/link";
import { redirect } from "next/navigation";

import { SetupPanel } from "@/components/app/setup-panel";
import { Button } from "@/components/ui/button";
import { getAppBootstrapState } from "@/lib/app-data";

export default async function AppEntryPage() {
  const bootstrap = await getAppBootstrapState();

  if (bootstrap.mode === "unconfigured") {
    return (
      <SetupPanel
        title="Add Clerk to enter the app"
        description="The application shell is wired and ready, but the web app still needs Clerk keys before protected routes can authenticate against Django."
        body="Set NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY and CLERK_SECRET_KEY in apps/web/.env.local. If Django expects a custom audience, set CLERK_JWT_TEMPLATE to the Clerk JWT template name that matches your backend verification setup."
      />
    );
  }

  if (bootstrap.mode === "signed-out") {
    redirect("/sign-in");
  }

  if (bootstrap.mode === "missing-token") {
    return (
      <SetupPanel
        title="Clerk is signed in but no backend token is available"
        description="The UI can see a signed-in Clerk session, but it could not mint the token the Django API expects."
        body="If your Django backend verifies a specific audience claim, create a Clerk JWT template with that audience and set CLERK_JWT_TEMPLATE in apps/web/.env.local."
      />
    );
  }

  const firstOrganization = bootstrap.organizations[0]?.organization;

  if (firstOrganization) {
    redirect(`/app/${firstOrganization.id}`);
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-4xl items-center px-6 py-16 sm:px-8">
      <section className="glass-panel ambient-border w-full rounded-[2.5rem] p-8 shadow-[0_30px_70px_rgba(44,37,29,0.1)] sm:p-10">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">No organization access</p>
        <h1 className="mt-4 text-4xl text-primary sm:text-5xl">Your account is signed in, but it does not belong to an organization yet.</h1>
        <p className="mt-4 max-w-2xl text-lg leading-8 text-muted-foreground">
          Ask an admin to create an active organization membership for your synced Django user, or use the sample seed data and match your Clerk identity to one of those memberships.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Button asChild>
            <Link href="/">Back to landing page</Link>
          </Button>
        </div>
      </section>
    </main>
  );
}
