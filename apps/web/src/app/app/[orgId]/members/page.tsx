import { redirect } from "next/navigation";

import { getGroups, getMembers } from "@/lib/api/app";
import { getOrganizationAppData } from "@/lib/app-data";
import { formatRole, formatVoicePart } from "@/lib/format";

type SearchParams = Promise<{
  search?: string;
  status?: string;
  voice_part?: string;
  type?: string;
}>;

type PageProps = {
  params: Promise<{ orgId: string }>;
  searchParams: SearchParams;
};

export default async function MembersPage({ params, searchParams }: PageProps) {
  const [{ orgId }, filters] = await Promise.all([params, searchParams]);
  const state = await getOrganizationAppData(orgId);

  if (state.mode !== "ready" || !state.context.organization) {
    return null;
  }

  if (!state.context.permissions.can_view_members) {
    if (state.context.permissions.can_view_directory) {
      redirect(`/app/${orgId}/directory`);
    }

    redirect(`/app/${orgId}`);
  }

  const [members, groups] = await Promise.all([
    getMembers(state.token, orgId, {
      search: filters.search,
      status: filters.status,
      voice_part: filters.voice_part,
    }),
    getGroups(state.token, orgId, filters.type),
  ]);

  return (
    <div className="space-y-6">
      <section className="glass-panel ambient-border rounded-[2.5rem] p-7 shadow-[0_22px_50px_rgba(38,35,29,0.08)] sm:p-8">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">Members</p>
        <h1 className="mt-4 text-5xl text-primary sm:text-6xl">Staff-facing member records and section structure.</h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 text-muted-foreground">
          This view uses the full member endpoint, including linked user IDs, notes-ready records, and group membership summaries.
        </p>
      </section>

      <section className="glass-panel ambient-border rounded-[2rem] p-5 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
        <form className="grid gap-4 md:grid-cols-4">
          <input
            name="search"
            defaultValue={filters.search ?? ""}
            placeholder="Search name or email"
            className="rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm outline-none ring-0 transition focus:border-primary/30"
          />
          <select name="voice_part" defaultValue={filters.voice_part ?? ""} className="rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm outline-none transition focus:border-primary/30">
            <option value="">All voice parts</option>
            <option value="soprano">Soprano</option>
            <option value="alto">Alto</option>
            <option value="tenor">Tenor</option>
            <option value="bass">Bass</option>
            <option value="mezzo_soprano">Mezzo soprano</option>
            <option value="baritone">Baritone</option>
            <option value="other">Other</option>
          </select>
          <select name="status" defaultValue={filters.status ?? ""} className="rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm outline-none transition focus:border-primary/30">
            <option value="">Any status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
          <button type="submit" className="rounded-2xl bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground shadow-[0_14px_30px_rgba(16,66,91,0.18)] transition hover:-translate-y-0.5 hover:bg-primary/95">
            Apply filters
          </button>
        </form>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <article className="glass-panel ambient-border rounded-[2.25rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">Member records</p>
              <p className="mt-2 text-sm text-muted-foreground">{members.length} records returned from Django</p>
            </div>
          </div>
          <div className="mt-6 space-y-4">
            {members.map((member) => (
              <article key={member.id} className="rounded-[1.5rem] border border-white/70 bg-white/72 p-5 backdrop-blur">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <h2 className="text-2xl text-primary">{member.first_name} {member.last_name}</h2>
                    <p className="mt-2 text-sm leading-7 text-muted-foreground">
                      {member.email}
                      {member.phone ? ` · ${member.phone}` : ""}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-primary/8 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
                      {formatVoicePart(member.voice_part)}
                    </span>
                    <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-foreground/70">
                      {member.status}
                    </span>
                  </div>
                </div>
                <div className="mt-4 grid gap-2 text-sm text-foreground/75 sm:grid-cols-2">
                  <p>Linked user: {member.user_id ? "Connected" : "Not linked"}</p>
                  <p>Joined: {member.joined_at ?? "Not set"}</p>
                </div>
              </article>
            ))}
            {members.length === 0 ? (
              <div className="rounded-[1.5rem] border border-dashed border-border bg-white/55 p-6 text-sm leading-7 text-muted-foreground">
                No members matched the current filter set.
              </div>
            ) : null}
          </div>
        </article>

        <article className="glass-panel ambient-border rounded-[2.25rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">Groups and sections</p>
          <div className="mt-6 space-y-4">
            {groups.map((group) => (
              <article key={group.id} className="rounded-[1.5rem] border border-white/70 bg-white/72 p-5 backdrop-blur">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h2 className="text-2xl text-primary">{group.name}</h2>
                    <p className="mt-2 text-sm leading-7 text-muted-foreground">{group.description || formatRole(group.type)}</p>
                  </div>
                  <span className="rounded-full bg-primary/8 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-primary">
                    {group.members.length} members
                  </span>
                </div>
              </article>
            ))}
            {groups.length === 0 ? (
              <div className="rounded-[1.5rem] border border-dashed border-border bg-white/55 p-6 text-sm leading-7 text-muted-foreground">
                No groups matched the current filter set.
              </div>
            ) : null}
          </div>
        </article>
      </section>
    </div>
  );
}
