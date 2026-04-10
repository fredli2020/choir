import { redirect } from "next/navigation";

import { getEvents, getMyEventResponses, getRelevantEvents } from "@/lib/api/app";
import { getOrganizationAppData } from "@/lib/app-data";
import { formatAudienceLabel, formatDateTime, formatEventType } from "@/lib/format";

type SearchParams = Promise<{
  search?: string;
  type?: string;
  upcoming?: string;
}>;

type PageProps = {
  params: Promise<{ orgId: string }>;
  searchParams: SearchParams;
};

export default async function EventsPage({ params, searchParams }: PageProps) {
  const [{ orgId }, filters] = await Promise.all([params, searchParams]);
  const state = await getOrganizationAppData(orgId);

  if (state.mode !== "ready" || !state.context.organization) {
    return null;
  }

  const permissions = state.context.permissions;

  if (!permissions.can_view_events && !permissions.can_view_relevant_events) {
    redirect(`/app/${orgId}`);
  }

  const eventPromise = permissions.can_view_events
    ? getEvents(state.token, orgId, {
        search: filters.search,
        type: filters.type,
        upcoming: filters.upcoming === "true",
      })
    : getRelevantEvents(state.token, orgId, {
        search: filters.search,
        type: filters.type,
      });

  const [events, responses] = await Promise.all([
    eventPromise,
    permissions.can_rsvp_to_events ? getMyEventResponses(state.token, orgId) : Promise.resolve([]),
  ]);

  return (
    <div className="space-y-6">
      <section className="glass-panel ambient-border rounded-[2.5rem] p-7 shadow-[0_22px_50px_rgba(38,35,29,0.08)] sm:p-8">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">Events</p>
        <h1 className="mt-4 text-5xl text-primary sm:text-6xl">Calendar and response state backed by real event data.</h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 text-muted-foreground">
          This page switches between org-wide events and relevant events based on backend capabilities, while keeping RSVP and attendance summaries distinct.
        </p>
      </section>

      <section className="glass-panel ambient-border rounded-[2rem] p-5 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
        <form className="grid gap-4 md:grid-cols-4">
          <input
            name="search"
            defaultValue={filters.search ?? ""}
            placeholder="Search event title"
            className="rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm outline-none transition focus:border-primary/30"
          />
          <select name="type" defaultValue={filters.type ?? ""} className="rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm outline-none transition focus:border-primary/30">
            <option value="">Any type</option>
            <option value="rehearsal">Rehearsal</option>
            <option value="performance">Performance</option>
            <option value="meeting">Meeting</option>
            <option value="other">Other</option>
          </select>
          <label className="flex items-center gap-3 rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm font-semibold text-foreground/76">
            <input type="checkbox" name="upcoming" value="true" defaultChecked={filters.upcoming === "true"} />
            Upcoming only
          </label>
          <button type="submit" className="rounded-2xl bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground shadow-[0_14px_30px_rgba(16,66,91,0.18)] transition hover:-translate-y-0.5 hover:bg-primary/95">
            Apply filters
          </button>
        </form>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <article className="glass-panel ambient-border rounded-[2.25rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">Event list</p>
          <div className="mt-6 space-y-4">
            {events.map((event) => (
              <article key={event.id} className="rounded-[1.5rem] border border-white/70 bg-white/72 p-5 backdrop-blur">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                      {formatEventType(event.type)}
                    </p>
                    <h2 className="mt-2 text-2xl text-primary">{event.title}</h2>
                    <p className="mt-2 text-sm leading-7 text-muted-foreground">
                      {formatDateTime(event.start_at, event.timezone)}
                      {event.location ? ` · ${event.location}` : ""}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-primary/8 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
                      {formatAudienceLabel(event.audience.audience_type)}
                    </span>
                    <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-foreground/70">
                      RSVP {event.my_rsvp?.status ?? "no_response"}
                    </span>
                  </div>
                </div>
                <div className="mt-4 grid gap-3 text-sm text-foreground/76 md:grid-cols-2">
                  <p>
                    RSVP: {event.rsvp_summary.yes} yes · {event.rsvp_summary.maybe} maybe · {event.rsvp_summary.no} no
                  </p>
                  <p>
                    Attendance: {event.attendance_summary.present} present · {event.attendance_summary.total_recorded}/{event.attendance_summary.total_targeted} recorded
                  </p>
                </div>
              </article>
            ))}
            {events.length === 0 ? (
              <div className="rounded-[1.5rem] border border-dashed border-border bg-white/55 p-6 text-sm leading-7 text-muted-foreground">
                No events matched the current filter set.
              </div>
            ) : null}
          </div>
        </article>

        <article className="glass-panel ambient-border rounded-[2.25rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">My responses</p>
          <div className="mt-6 space-y-4">
            {responses.slice(0, 6).map((response) => (
              <article key={response.event.id} className="rounded-[1.5rem] border border-white/70 bg-white/72 p-5 backdrop-blur">
                <h2 className="text-xl text-primary">{response.event.title}</h2>
                <p className="mt-2 text-sm leading-7 text-muted-foreground">
                  {formatDateTime(response.event.start_at, response.event.timezone)}
                </p>
                <p className="mt-3 text-xs font-semibold uppercase tracking-[0.22em] text-primary">
                  RSVP {response.status}
                </p>
                {response.note ? <p className="mt-2 text-sm leading-7 text-foreground/76">{response.note}</p> : null}
              </article>
            ))}
            {responses.length === 0 ? (
              <div className="rounded-[1.5rem] border border-dashed border-border bg-white/55 p-6 text-sm leading-7 text-muted-foreground">
                No RSVP responses are recorded for the current user yet.
              </div>
            ) : null}
          </div>
        </article>
      </section>
    </div>
  );
}
