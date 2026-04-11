import { redirect } from "next/navigation";

import { getGoogleCalendars, getGoogleCalendarConnectionStatus } from "@/lib/api/app";
import { getOrganizationAppData } from "@/lib/app-data";
import { formatDateTime } from "@/lib/format";

type SearchParams = Promise<{
  google_calendar?: string;
  detail?: string;
}>;

type PageProps = {
  params: Promise<{ orgId: string }>;
  searchParams: SearchParams;
};

const statusCopy: Record<string, string> = {
  connected: "Google account connected.",
  calendar_selected: "Google Calendar selected.",
  disconnected: "Google Calendar disconnected.",
  error: "Google Calendar action failed. Check the details below.",
};

export default async function GoogleCalendarSettingsPage({ params, searchParams }: PageProps) {
  const [{ orgId }, query] = await Promise.all([params, searchParams]);
  const state = await getOrganizationAppData(orgId);

  if (state.mode !== "ready" || !state.context.organization) {
    return null;
  }

  if (!state.context.permissions.can_manage_google_calendar) {
    redirect(`/app/${orgId}`);
  }

  const connection = await getGoogleCalendarConnectionStatus(state.token, orgId);
  const calendars =
    connection.connected ? await getGoogleCalendars(state.token, orgId).catch(() => []) : [];

  return (
    <div className="space-y-6">
      <section className="glass-panel ambient-border rounded-[2.5rem] p-7 shadow-[0_22px_50px_rgba(38,35,29,0.08)] sm:p-8">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">
          Google Calendar
        </p>
        <h1 className="mt-4 text-5xl text-primary sm:text-6xl">
          One-way event sync from Choir App to Google Calendar.
        </h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 text-muted-foreground">
          Local events stay authoritative. When sync is enabled, Django mirrors event changes to the selected Google Calendar and records any sync issues without rolling back local data.
        </p>
      </section>

      {query.google_calendar ? (
        <section className="glass-panel ambient-border rounded-[2rem] border border-amber-200 bg-amber-50/80 p-5 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-amber-900">
            {statusCopy[query.google_calendar] ?? "Google Calendar update"}
          </p>
          {query.detail ? (
            <p className="mt-2 text-sm leading-7 text-amber-950">{query.detail}</p>
          ) : null}
        </section>
      ) : null}

      <section className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <article className="glass-panel ambient-border rounded-[2.25rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">
            Connection status
          </p>
          <div className="mt-6 space-y-4">
            <div className="rounded-[1.5rem] border border-white/70 bg-white/72 p-5 backdrop-blur">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                OAuth
              </p>
              <p className="mt-2 text-2xl text-primary">
                {connection.oauth_configured ? "Configured" : "Missing credentials"}
              </p>
              <p className="mt-2 text-sm leading-7 text-muted-foreground">
                {connection.oauth_configured
                  ? "The backend has the Google client ID, secret, and callback URL it needs."
                  : "Set the Google OAuth environment variables in the Django app before connecting."}
              </p>
            </div>

            <div className="rounded-[1.5rem] border border-white/70 bg-white/72 p-5 backdrop-blur">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                Account
              </p>
              <p className="mt-2 text-2xl text-primary">
                {connection.connected ? connection.google_account_email : "Not connected"}
              </p>
              <p className="mt-2 text-sm leading-7 text-muted-foreground">
                {connection.calendar_id
                  ? `Selected calendar: ${connection.calendar_id}`
                  : "No Google Calendar has been selected yet."}
              </p>
              {connection.token_expiry ? (
                <p className="mt-2 text-sm leading-7 text-muted-foreground">
                  Access token expires {formatDateTime(connection.token_expiry, "UTC")}
                </p>
              ) : null}
            </div>

            {connection.last_sync_error ? (
              <div className="rounded-[1.5rem] border border-amber-200 bg-amber-50 p-5">
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-900">
                  Last sync issue
                </p>
                <p className="mt-2 text-sm leading-7 text-amber-950">{connection.last_sync_error}</p>
                {connection.last_sync_error_at ? (
                  <p className="mt-2 text-sm text-amber-900/80">
                    {formatDateTime(connection.last_sync_error_at, "UTC")}
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
        </article>

        <article className="glass-panel ambient-border rounded-[2.25rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">
            Controls
          </p>
          <div className="mt-6 space-y-5">
            <a
              href={`/api/google-calendar/start?orgId=${orgId}`}
              className="inline-flex rounded-2xl bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground shadow-[0_14px_30px_rgba(16,66,91,0.18)] transition hover:-translate-y-0.5 hover:bg-primary/95"
            >
              {connection.connected ? "Reconnect Google account" : "Connect Google account"}
            </a>

            {connection.connected ? (
              <form action="/api/google-calendar/select-calendar" method="POST" className="space-y-4 rounded-[1.5rem] border border-white/70 bg-white/72 p-5 backdrop-blur">
                <input type="hidden" name="orgId" value={orgId} />
                <div>
                  <label htmlFor="calendarId" className="text-sm font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                    Sync destination
                  </label>
                  <select
                    id="calendarId"
                    name="calendarId"
                    defaultValue={connection.calendar_id ?? ""}
                    className="mt-3 w-full rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm outline-none transition focus:border-primary/30"
                  >
                    <option value="" disabled>
                      Select a Google Calendar
                    </option>
                    {calendars.map((calendar) => (
                      <option key={calendar.id} value={calendar.id}>
                        {calendar.summary}
                        {calendar.primary ? " (Primary)" : ""}
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  type="submit"
                  className="rounded-2xl bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground shadow-[0_14px_30px_rgba(16,66,91,0.18)] transition hover:-translate-y-0.5 hover:bg-primary/95"
                >
                  Save calendar selection
                </button>
              </form>
            ) : null}

            {connection.connected ? (
              <form action="/api/google-calendar/disconnect" method="POST">
                <input type="hidden" name="orgId" value={orgId} />
                <button
                  type="submit"
                  className="rounded-2xl border border-border bg-white/80 px-5 py-3 text-sm font-semibold text-foreground shadow-[0_14px_30px_rgba(35,34,29,0.08)] transition hover:-translate-y-0.5"
                >
                  Disconnect Google Calendar
                </button>
              </form>
            ) : null}
          </div>
        </article>
      </section>
    </div>
  );
}
