import { CalendarClock, CheckCircle2, Sparkles, UsersRound } from "lucide-react";

import { getDirectory, getGroups, getMembers, getUpcomingEvents } from "@/lib/api/app";
import { getOrganizationAppData } from "@/lib/app-data";
import { formatDateTime, formatRole, formatVoicePart } from "@/lib/format";

type PageProps = {
  params: Promise<{ orgId: string }>;
};

export default async function OrganizationDashboardPage({ params }: PageProps) {
  const { orgId } = await params;
  const state = await getOrganizationAppData(orgId);

  if (state.mode !== "ready" || !state.context.organization || !state.context.membership) {
    return null;
  }

  const { permissions } = state.context;

  const [upcomingEvents, peoplePreview, groups] = await Promise.all([
    permissions.can_view_relevant_events ? getUpcomingEvents(state.token, orgId) : Promise.resolve([]),
    permissions.can_view_members
      ? getMembers(state.token, orgId, { status: "active" })
      : permissions.can_view_directory
        ? getDirectory(state.token, orgId, { status: "active" })
        : Promise.resolve([]),
    permissions.can_view_members ? getGroups(state.token, orgId) : Promise.resolve([]),
  ]);

  const cards = [
    {
      label: "Current role",
      value: formatRole(state.context.membership.role),
      detail: "Resolved from Django membership context",
      icon: Sparkles,
    },
    {
      label: "Visible people",
      value: String(peoplePreview.length),
      detail: permissions.can_view_members ? "Member records available" : "Directory entries available",
      icon: UsersRound,
    },
    {
      label: "Upcoming events",
      value: String(upcomingEvents.length),
      detail: "Relevant to the current user and organization",
      icon: CalendarClock,
    },
    {
      label: "Recorded capabilities",
      value: String(Object.values(permissions).filter(Boolean).length),
      detail: "Capabilities currently enabled in the backend",
      icon: CheckCircle2,
    },
  ];

  return (
    <div className="space-y-6">
      <section className="glass-panel ambient-border rounded-[2.5rem] p-7 shadow-[0_22px_50px_rgba(38,35,29,0.08)] sm:p-8">
        <p className="text-sm font-semibold uppercase tracking-[0.26em] text-muted-foreground">Overview</p>
        <h1 className="mt-4 text-balance text-5xl text-primary sm:text-6xl">
          {state.context.organization.name} is ready for day-to-day choir operations.
        </h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 text-muted-foreground">
          This shell is pulling authenticated user context, organization membership, permissions, people data, and relevant events directly from the Django API.
        </p>
      </section>

      <section className="grid gap-4 xl:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <article key={card.label} className="glass-panel ambient-border rounded-[2rem] p-5 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
              <div className="flex items-center justify-between gap-4">
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">{card.label}</p>
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                  <Icon className="h-5 w-5" />
                </div>
              </div>
              <p className="mt-5 text-3xl font-semibold text-primary">{card.value}</p>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">{card.detail}</p>
            </article>
          );
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <article className="glass-panel ambient-border rounded-[2.25rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">Upcoming events</p>
          <div className="mt-6 space-y-4">
            {upcomingEvents.length > 0 ? (
              upcomingEvents.slice(0, 4).map((event) => (
                <div key={event.id} className="rounded-[1.5rem] border border-white/70 bg-white/72 p-5 backdrop-blur">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">{event.type}</p>
                      <h2 className="mt-2 text-2xl text-primary">{event.title}</h2>
                      <p className="mt-2 text-sm leading-7 text-muted-foreground">
                        {formatDateTime(event.start_at, event.timezone)}
                        {event.location ? ` · ${event.location}` : ""}
                      </p>
                    </div>
                    <div className="rounded-full bg-primary/8 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
                      RSVP {event.my_rsvp?.status ?? "no_response"}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-[1.5rem] border border-dashed border-border bg-white/55 p-6 text-sm leading-7 text-muted-foreground">
                No relevant upcoming events are available for this organization context yet.
              </div>
            )}
          </div>
        </article>

        <div className="grid gap-6">
          <article className="glass-panel ambient-border rounded-[2.25rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">People snapshot</p>
            <div className="mt-6 space-y-3">
              {peoplePreview.slice(0, 5).map((person) => (
                <div key={person.id} className="flex items-center justify-between rounded-[1.4rem] bg-white/72 px-4 py-3 backdrop-blur">
                  <div>
                    <p className="font-semibold text-foreground">{person.first_name} {person.last_name}</p>
                    <p className="text-sm text-muted-foreground">{person.email}</p>
                  </div>
                  <span className="rounded-full bg-primary/8 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
                    {formatVoicePart(person.voice_part)}
                  </span>
                </div>
              ))}
              {peoplePreview.length === 0 ? (
                <div className="rounded-[1.5rem] border border-dashed border-border bg-white/55 p-6 text-sm leading-7 text-muted-foreground">
                  No people are visible with the current capability set.
                </div>
              ) : null}
            </div>
          </article>

          <article className="glass-panel ambient-border rounded-[2.25rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">Groups and sections</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {groups.slice(0, 8).map((group) => (
                <span key={group.id} className="rounded-full border border-primary/10 bg-primary/6 px-3 py-2 text-sm font-semibold text-primary">
                  {group.name}
                </span>
              ))}
              {groups.length === 0 ? (
                <p className="text-sm leading-7 text-muted-foreground">
                  Group data will appear here for roles that can view members.
                </p>
              ) : null}
            </div>
          </article>
        </div>
      </section>
    </div>
  );
}
