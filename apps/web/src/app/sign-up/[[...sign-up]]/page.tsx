import { SignUp } from "@clerk/nextjs";

import { SetupPanel } from "@/components/app/setup-panel";
import { isClerkConfigured } from "@/lib/server-env";

export default function SignUpPage() {
  if (!isClerkConfigured()) {
    return (
      <SetupPanel
        title="Clerk is not configured yet"
        description="The sign-up screen is ready, but the web app still needs Clerk environment variables before it can render the Clerk UI."
        body="Set NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY and CLERK_SECRET_KEY in apps/web/.env.local. If Django verifies a custom audience, also set CLERK_JWT_TEMPLATE so the frontend sends the expected token."
      />
    );
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl items-center justify-center px-6 py-12 sm:px-8 lg:px-10">
      <div className="glass-panel ambient-border rounded-[2.5rem] p-4 shadow-[0_28px_70px_rgba(33,31,26,0.1)]">
        <SignUp signInUrl="/sign-in" />
      </div>
    </main>
  );
}
