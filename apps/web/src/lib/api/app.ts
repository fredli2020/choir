import "server-only";

import { apiFetch } from "@/lib/api/client";
import type {
  CurrentUser,
  CurrentUserContext,
  DirectoryMember,
  EventRecord,
  GoogleCalendarChoice,
  GoogleCalendarConnectionStatus,
  Group,
  MemberProfile,
  MyEventResponse,
  OrganizationSummary,
} from "@/types/api";

export async function getCurrentUser(token: string) {
  return apiFetch<CurrentUser>("/api/me", { token });
}

export async function getCurrentUserOrganizations(token: string) {
  return apiFetch<OrganizationSummary[]>("/api/me/organizations", { token });
}

export async function getCurrentUserContext(token: string, organizationId: string) {
  return apiFetch<CurrentUserContext>("/api/me/context", {
    token,
    searchParams: { organization_id: organizationId },
  });
}

export async function getMembers(
  token: string,
  organizationId: string,
  filters?: {
    search?: string;
    status?: string;
    voice_part?: string;
  },
) {
  return apiFetch<MemberProfile[]>(`/api/orgs/${organizationId}/members`, {
    token,
    searchParams: filters,
  });
}

export async function getDirectory(
  token: string,
  organizationId: string,
  filters?: {
    search?: string;
    status?: string;
    voice_part?: string;
  },
) {
  return apiFetch<DirectoryMember[]>(`/api/orgs/${organizationId}/directory`, {
    token,
    searchParams: filters,
  });
}

export async function getMyProfile(token: string, organizationId: string) {
  return apiFetch<MemberProfile>(`/api/orgs/${organizationId}/my-profile`, { token });
}

export async function getGroups(token: string, organizationId: string, type?: string) {
  return apiFetch<Group[]>(`/api/orgs/${organizationId}/groups`, {
    token,
    searchParams: { type },
  });
}

export async function getEvents(
  token: string,
  organizationId: string,
  filters?: {
    search?: string;
    type?: string;
    upcoming?: boolean;
  },
) {
  return apiFetch<EventRecord[]>(`/api/orgs/${organizationId}/events`, {
    token,
    searchParams: filters,
  });
}

export async function getRelevantEvents(
  token: string,
  organizationId: string,
  filters?: {
    search?: string;
    type?: string;
  },
) {
  return apiFetch<EventRecord[]>(`/api/orgs/${organizationId}/events/relevant`, {
    token,
    searchParams: filters,
  });
}

export async function getUpcomingEvents(token: string, organizationId: string) {
  return apiFetch<EventRecord[]>(`/api/orgs/${organizationId}/events/upcoming`, {
    token,
  });
}

export async function getMyEventResponses(token: string, organizationId: string) {
  return apiFetch<MyEventResponse[]>(`/api/orgs/${organizationId}/events/my-responses`, {
    token,
  });
}

export async function getGoogleCalendarConnectionStatus(token: string, organizationId: string) {
  return apiFetch<GoogleCalendarConnectionStatus>(
    `/api/orgs/${organizationId}/integrations/google-calendar`,
    { token },
  );
}

export async function getGoogleCalendars(token: string, organizationId: string) {
  const payload = await apiFetch<{ calendars: GoogleCalendarChoice[] }>(
    `/api/orgs/${organizationId}/integrations/google-calendar/calendars`,
    { token },
  );
  return payload.calendars;
}
