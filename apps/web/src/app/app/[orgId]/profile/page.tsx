import { redirect } from "next/navigation";

import { SetupPanel } from "@/components/app/setup-panel";
import { ApiClientError } from "@/lib/api/client";
import { getMyProfile } from "@/lib/api/app";
import { getOrganizationAppData } from "@/lib/app-data";
import { formatDate, formatVoicePart } from "@/lib/format";

type PageProps = {
  params: Promise<{ orgId: string }>;
};

export default async function ProfilePage({ params }: PageProps) {
  const { orgId } = await params;
  const state = await getOrganizationAppData(orgId);

  if (state.mode !== "ready" || !state.context.organization) {
    return null;
  }

  if (!state.context.permissions.can_self_edit_profile) {
    redirect(`/app/${orgId}`);
  }

  try {
    const profile = await getMyProfile(state.token, orgId);

    return (
      <div className="space-y-6">
        <section className="glass-panel ambient-border rounded-[2.5rem] p-7 shadow-[0_22px_50px_rgba(38,35,29,0.08)] sm:p-8">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-muted-foreground">My profile</p>
          <h1 className="mt-4 text-5xl text-primary sm:text-6xl">Your linked member profile for this organization.</h1>
          <p className="mt-4 max-w-3xl text-lg leading-8 text-muted-foreground">
            The profile surface is reading the same organization-scoped member profile the backend uses for RSVP and relevant event access.
          </p>
        </section>

        <section className="glass-panel ambient-border rounded-[2.25rem] p-6 shadow-[0_18px_40px_rgba(35,34,29,0.08)]">
          <div className="grid gap-5 md:grid-cols-2">
            <article className="rounded-[1.5rem] border border-white/70 bg-white/72 p-5 backdrop-blur">
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-muted-foreground">Identity</p>
              <h2 className="mt-3 text-3xl text-primary">{profile.first_name} {profile.last_name}</h2>
              <div className="mt-4 space-y-2 text-sm leading-7 text-muted-foreground">
                <p>{profile.email}</p>
                <p>{profile.phone || "No phone on file"}</p>
              </div>
            </article>
            <article className="rounded-[1.5rem] border border-white/70 bg-white/72 p-5 backdrop-blur">
              <p className="text-sm font-semibold uppercase tracking-[0.22em] text-muted-foreground">Choir details</p>
              <div className="mt-4 space-y-2 text-sm leading-7 text-muted-foreground">
                <p>Voice part: {formatVoicePart(profile.voice_part)}</p>
                <p>Status: {profile.status}</p>
                <p>Joined: {profile.joined_at ? formatDate(profile.joined_at) : "Not set"}</p>
              </div>
            </article>
          </div>
        </section>
      </div>
    );
  } catch (error) {
    if (error instanceof ApiClientError) {
      return (
        <SetupPanel
          title="No linked member profile yet"
          description="Your account is authenticated, but this organization does not have an active member profile linked to your user yet."
          body="A linked active member profile is required for self-service profile views and member-specific RSVP workflows. An admin can create or link the profile in the Django admin or member management surface."
          ctaHref={`/app/${orgId}`}
          ctaLabel="Back to overview"
        />
      );
    }

    throw error;
  }
}
