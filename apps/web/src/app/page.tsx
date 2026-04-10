import { Button } from "@/components/ui/button";
import { getHealthSummary } from "@/lib/api/health";
import { appConfig } from "@/lib/config";

export default async function HomePage() {
  const health = await getHealthSummary();

  return (
    <main className="mx-auto flex min-h-screen max-w-5xl flex-col gap-10 px-6 py-16">
      <section className="space-y-6">
        <p className="text-sm font-medium uppercase tracking-[0.3em] text-muted-foreground">
          Choir management scaffold
        </p>
        <div className="space-y-4">
          <h1 className="max-w-3xl text-5xl font-semibold tracking-tight text-primary">
            Backend-first foundation for a production-quality choir app.
          </h1>
          <p className="max-w-2xl text-lg leading-8 text-muted-foreground">
            This starter keeps the UI thin, routes all business logic through the Django API,
            and leaves room for organizations, people, events, attendance, and future calendar
            sync without turning the codebase into a pile of early abstractions.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button asChild>
            <a href={`${appConfig.apiBaseUrl}/api/health/live`} target="_blank" rel="noreferrer">
              Open API health check
            </a>
          </Button>
          <Button asChild variant="secondary">
            <a href="https://nextjs.org/docs" target="_blank" rel="noreferrer">
              Next.js docs
            </a>
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-3xl border bg-card p-6 shadow-sm">
          <p className="text-sm uppercase tracking-[0.25em] text-muted-foreground">API base URL</p>
          <p className="mt-4 text-xl font-semibold text-card-foreground">{appConfig.apiBaseUrl}</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Configured through <code>NEXT_PUBLIC_API_BASE_URL</code>.
          </p>
        </article>

        <article className="rounded-3xl border bg-card p-6 shadow-sm">
          <p className="text-sm uppercase tracking-[0.25em] text-muted-foreground">Health status</p>
          <p className="mt-4 text-xl font-semibold text-card-foreground">{health.label}</p>
          <p className="mt-2 text-sm text-muted-foreground">{health.detail}</p>
        </article>
      </section>
    </main>
  );
}
