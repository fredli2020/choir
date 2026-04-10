import { redirect } from "next/navigation";

import { getDirectory } from "@/lib/api/app";
import { getOrganizationAppData } from "@/lib/app-data";
import { formatVoicePart } from "@/lib/format";

type SearchParams = Promise<{
  search?: string;
  status?: string;
  voice_part?: string;
}>;

type PageProps = {
  params: Promise<{ orgId: string }>;
  searchParams: SearchParams;
};

export default async function DirectoryPage({ params, searchParams }: PageProps) {
  const [{ orgId }, filters] = await Promise.all([params, searchParams]);
  const state = await getOrganizationAppData(orgId);

  if (state.mode !== "ready" || !state.context.organization) {
    return null;
  }

  if (!state.context.permissions.can_view_directory) {
    redirect(`/app/${orgId}`);
  }

  const directory = await getDirectory(state.token, orgId, {
    search: filters.search,
    status: filters.status,
    voice_part: filters.voice_part,
  });

  return (
    <div className="space-y-6">
      <section className="glass-panel ambient-border rounded-[2.5rem] p-7 shadow-[0_22px_50px_rgba(38,35,29,0.08)] sm:p-8">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">Directory</p>
        <h1 className="mt-4 text-5xl text-primary sm:text-6xl">A clean member directory that respects backend policy.</h1>
        <p className="mt-4 max-w-3xl text-lg leading-8 text-muted-foreground">
          This page uses the limited directory endpoint rather than the full staff member record surface.
        </p>
      </section>

      <section className="glass-panel ambient-border rounded-[2rem] p-5 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
        <form className="grid gap-4 md:grid-cols-4">
          <input
            name="search"
            defaultValue={filters.search ?? ""}
            placeholder="Search name or email"
            className="rounded-2xl border border-white/70 bg-white/80 px-4 py-3 text-sm outline-none transition focus:border-primary/30"
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

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {directory.map((member) => (
          <article key={member.id} className="glass-panel ambient-border rounded-[2rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
            <h2 className="text-2xl text-primary">{member.first_name} {member.last_name}</h2>
            <div className="mt-4 space-y-2 text-sm leading-7 text-muted-foreground">
              <p>{member.email}</p>
              <p>{member.phone || "No phone on file"}</p>
              <p>{formatVoicePart(member.voice_part)}</p>
            </div>
          </article>
        ))}
        {directory.length === 0 ? (
          <div className="glass-panel ambient-border rounded-[2rem] p-6 text-sm leading-7 text-muted-foreground shadow-[0_18px_40px_rgba(35,34,29,0.08)] md:col-span-2 xl:col-span-3">
            No directory records matched the current filters.
          </div>
        ) : null}
      </section>
    </div>
  );
}
