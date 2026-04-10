import Link from "next/link";
import { redirect } from "next/navigation";
import {
  ArrowRight,
  CalendarRange,
  Orbit,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { getServerAuthState } from "@/lib/auth";
import { getHealthSummary } from "@/lib/api/health";
import { appConfig } from "@/lib/config";

const featureCards = [
  {
    title: "Operational clarity",
    description:
      "Organizations, members, groups, events, RSVPs, and attendance already live behind one clean API.",
    icon: Users,
  },
  {
    title: "Backend-enforced access",
    description:
      "The frontend now reads organization context and capabilities from Django instead of guessing at raw roles.",
    icon: ShieldCheck,
  },
  {
    title: "Ready for richer portals",
    description:
      "The shell is designed to expand into member and staff workflows without another redesign pass first.",
    icon: Orbit,
  },
];

export default async function HomePage() {
  const authState = await getServerAuthState();
  const health = await getHealthSummary();

  if (authState.userId) {
    redirect("/app");
  }

  return (
    <main className="relative overflow-hidden">
      <div className="hero-orb left-[-8rem] top-[6rem] h-56 w-56 bg-[rgba(246,193,92,0.38)]" />
      <div className="hero-orb right-[6%] top-[9rem] h-72 w-72 bg-[rgba(76,135,160,0.18)] soft-float" />
      <div className="hero-orb bottom-[18%] right-[-5rem] h-48 w-48 bg-[rgba(220,117,81,0.18)]" />

      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-6 pb-20 pt-6 sm:px-8 lg:px-10">
        <header className="glass-panel ambient-border sticky top-5 z-20 mb-12 flex items-center justify-between rounded-full px-4 py-3 fade-up sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-[0_12px_24px_rgba(17,67,92,0.22)]">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold tracking-[0.18em] text-foreground/60 uppercase">
                Choir App
              </p>
              <p className="text-sm text-muted-foreground">Modern choir operations</p>
            </div>
          </div>

          <div className="hidden items-center gap-2 md:flex">
            <Button asChild variant="ghost">
              <a href="#product">Product</a>
            </Button>
            <Button asChild variant="ghost">
              <a href="#foundation">Foundation</a>
            </Button>
          </div>
        </header>

        <section className="grid items-start gap-12 pb-20 lg:grid-cols-[1.1fr_0.9fr] lg:pb-28">
          <div className="space-y-8">
            <div className="fade-up space-y-5">
              <div className="inline-flex items-center gap-3 rounded-full border border-white/70 bg-white/65 px-4 py-2 text-sm text-foreground/72 shadow-[0_10px_32px_rgba(29,35,39,0.06)] backdrop-blur">
                <CalendarRange className="h-4 w-4 text-[hsl(var(--accent))]" />
                Auth-aware dashboard shell now wired to the Django API
              </div>
              <h1 className="max-w-4xl text-balance text-6xl leading-[0.94] text-primary sm:text-7xl lg:text-[5.6rem]">
                Choir software that finally looks and behaves like a real product.
              </h1>
              <p className="max-w-2xl text-lg leading-8 text-muted-foreground sm:text-xl">
                The frontend now has a real landing page, Clerk-ready auth entry points, and an org-aware application shell for members, directory, and event workflows.
              </p>
            </div>

            <div className="fade-up fade-up-delay-1 flex flex-wrap gap-3">
              <Button asChild className="sheen">
                <Link href={authState.clerkConfigured ? appConfig.signInUrl : "#foundation"}>
                  {authState.clerkConfigured ? "Open the app" : "Finish Clerk setup"}
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="secondary" className="sheen">
                <a href={appConfig.apiBaseUrl + "/api/health/ready"} target="_blank" rel="noreferrer">
                  Check backend readiness
                </a>
              </Button>
            </div>

            <div className="fade-up fade-up-delay-2 grid gap-4 sm:grid-cols-3">
              <article className="glass-panel ambient-border rounded-[2rem] p-5 shadow-[0_16px_34px_rgba(36,34,29,0.06)]">
                <p className="text-3xl font-semibold text-primary sm:text-4xl">{authState.clerkConfigured ? "Live" : "Setup"}</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  Clerk wiring {authState.clerkConfigured ? "is ready for sign-in routes" : "still needs env keys"}
                </p>
              </article>
              <article className="glass-panel ambient-border rounded-[2rem] p-5 shadow-[0_16px_34px_rgba(36,34,29,0.06)]">
                <p className="text-3xl font-semibold text-primary sm:text-4xl">{health.label === "API reachable" ? "200" : "Warn"}</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">{health.detail}</p>
              </article>
              <article className="glass-panel ambient-border rounded-[2rem] p-5 shadow-[0_16px_34px_rgba(36,34,29,0.06)]">
                <p className="text-3xl font-semibold text-primary sm:text-4xl">3</p>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  first-class app surfaces: dashboard, members, and events
                </p>
              </article>
            </div>
          </div>

          <div className="fade-up fade-up-delay-2 lg:pl-6">
            <div className="glass-panel ambient-border overflow-hidden rounded-[2rem] p-6 shadow-[0_30px_70px_rgba(44,37,29,0.1)]">
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">
                What is wired now
              </p>
              <h2 className="mt-4 text-4xl text-primary">A real app shell, not a placeholder route.</h2>
              <div className="mt-8 grid gap-4">
                {featureCards.map((feature) => {
                  const Icon = feature.icon;
                  return (
                    <article key={feature.title} className="rounded-[1.5rem] border border-white/70 bg-white/72 p-5 backdrop-blur">
                      <div className="flex items-start gap-4">
                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                          <Icon className="h-5 w-5" />
                        </div>
                        <div>
                          <h3 className="text-2xl text-primary">{feature.title}</h3>
                          <p className="mt-2 text-sm leading-7 text-muted-foreground">{feature.description}</p>
                        </div>
                      </div>
                    </article>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        <section id="product" className="grid gap-6 pb-20 lg:grid-cols-3 lg:pb-28">
          <article className="glass-panel ambient-border rounded-[2rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)] fade-up">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">Dashboard</p>
            <h2 className="mt-4 text-3xl text-primary">Org context, role, upcoming work, and live API state.</h2>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              Signed-in users land in an org-aware shell that reads memberships and permissions from the backend.
            </p>
          </article>
          <article className="glass-panel ambient-border rounded-[2rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)] fade-up fade-up-delay-1">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">Members</p>
            <h2 className="mt-4 text-3xl text-primary">Staff-facing members view and member-safe directory view.</h2>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              The UI chooses the right endpoint based on capabilities instead of duplicating backend role logic in React.
            </p>
          </article>
          <article className="glass-panel ambient-border rounded-[2rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)] fade-up fade-up-delay-2">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">Events</p>
            <h2 className="mt-4 text-3xl text-primary">Relevant events, RSVP state, and attendance signal.</h2>
            <p className="mt-3 text-sm leading-7 text-muted-foreground">
              Event cards already surface audience, RSVP, and attendance summaries from the Django API.
            </p>
          </article>
        </section>

        <section id="foundation" className="fade-up">
          <div className="glass-panel ambient-border rounded-[2.6rem] px-7 py-10 shadow-[0_28px_70px_rgba(33,31,26,0.1)] sm:px-10">
            <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
              <div className="max-w-3xl space-y-4">
                <p className="text-sm font-semibold uppercase tracking-[0.28em] text-muted-foreground">
                  Local auth setup
                </p>
                <h2 className="text-balance text-5xl text-primary sm:text-6xl">
                  Add Clerk env keys to light up the signed-in app shell on localhost.
                </h2>
                <p className="text-lg leading-8 text-muted-foreground">
                  Set the publishable key and secret in the web app, then optionally configure a Clerk JWT template if your Django backend expects a specific audience claim.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button asChild>
                  <Link href={authState.clerkConfigured ? appConfig.signInUrl : "/#foundation"}>
                    {authState.clerkConfigured ? "Go to sign in" : "Add Clerk env"}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                <Button asChild variant="secondary">
                  <a href="https://clerk.com/docs" target="_blank" rel="noreferrer">
                    View Clerk docs
                  </a>
                </Button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}
