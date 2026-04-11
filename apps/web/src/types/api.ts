export type Uuid = string;

export type HealthResponse = {
  status: "ok" | "error";
  database?: boolean;
};

export type CurrentUser = {
  id: Uuid;
  auth_provider_id: string;
  email: string;
  name: string;
  created_at: string;
  updated_at: string;
};

export type Organization = {
  id: Uuid;
  name: string;
  slug: string;
  created_at: string;
  updated_at: string;
};

export type OrganizationMembership = {
  id: Uuid;
  role: "admin" | "section_leader" | "member";
  status: string;
  created_at: string;
  updated_at: string;
};

export type OrganizationSummary = {
  organization: Organization;
  membership: OrganizationMembership;
};

export type OrganizationPermissions = {
  can_manage_members: boolean;
  can_manage_groups: boolean;
  can_view_members: boolean;
  can_manage_events: boolean;
  can_view_events: boolean;
  can_view_relevant_events: boolean;
  can_rsvp_to_events: boolean;
  can_record_attendance: boolean;
  can_send_messages: boolean;
  can_manage_google_calendar: boolean;
  can_view_directory: boolean;
  can_self_edit_profile: boolean;
};

export type CurrentUserContext = {
  user: CurrentUser;
  organization: Organization | null;
  membership: OrganizationMembership | null;
  permissions: OrganizationPermissions;
};

export type MemberProfile = {
  id: Uuid;
  organization_id: Uuid;
  user_id: Uuid | null;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  voice_part:
    | "soprano"
    | "alto"
    | "tenor"
    | "bass"
    | "mezzo_soprano"
    | "baritone"
    | "other"
    | null;
  status: "active" | "inactive";
  notes: string | null;
  joined_at: string | null;
  created_at: string;
  updated_at: string;
};

export type DirectoryMember = {
  id: Uuid;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  voice_part: MemberProfile["voice_part"];
  status: MemberProfile["status"];
};

export type GroupMember = {
  id: Uuid;
  member_profile_id: Uuid;
  first_name: string;
  last_name: string;
  email: string;
  voice_part: MemberProfile["voice_part"];
  role: string | null;
  created_at: string;
};

export type Group = {
  id: Uuid;
  organization_id: Uuid;
  type: "section" | "committee" | "ensemble" | "other";
  name: string;
  description: string | null;
  members: GroupMember[];
  created_at: string;
  updated_at: string;
};

export type EventAudience = {
  audience_type: "all_members" | "group" | "selected_members" | null;
  group: { id: Uuid; type: Group["type"]; name: string } | null;
  selected_members: Array<{
    id: Uuid;
    first_name: string;
    last_name: string;
    email: string;
    voice_part: MemberProfile["voice_part"];
    status: MemberProfile["status"];
  }>;
  member_count: number;
};

export type EventRsvpSummary = {
  yes: number;
  no: number;
  maybe: number;
  no_response: number;
  total_targeted: number;
};

export type EventAttendanceSummary = {
  present: number;
  absent: number;
  late: number;
  excused: number;
  total_recorded: number;
  total_targeted: number;
};

export type CurrentMemberRsvp = {
  status: "yes" | "no" | "maybe" | "no_response";
  note: string | null;
  responded_at: string | null;
  updated_at: string | null;
};

export type GoogleCalendarSyncStatus = {
  status: "not_synced" | "linked" | "synced" | "failed";
  last_synced_at: string | null;
  error: string | null;
};

export type EventRecord = {
  id: Uuid;
  organization_id: Uuid;
  title: string;
  description: string | null;
  type: "rehearsal" | "performance" | "meeting" | "other";
  location: string | null;
  start_at: string;
  end_at: string;
  timezone: string;
  is_all_day: boolean;
  google_calendar_event_id: string | null;
  google_calendar_sync: GoogleCalendarSyncStatus;
  created_by_user_id: Uuid | null;
  audience: EventAudience;
  rsvp_summary: EventRsvpSummary;
  attendance_summary: EventAttendanceSummary;
  my_rsvp: CurrentMemberRsvp | null;
  created_at: string;
  updated_at: string;
};

export type MyEventResponse = {
  event: EventRecord;
  status: CurrentMemberRsvp["status"];
  note: string | null;
  responded_at: string | null;
  updated_at: string | null;
};

export type GoogleCalendarConnectionStatus = {
  oauth_configured: boolean;
  connected: boolean;
  google_account_email: string | null;
  calendar_id: string | null;
  token_expiry: string | null;
  last_sync_error: string | null;
  last_sync_error_at: string | null;
  last_calendar_sync_at: string | null;
};

export type GoogleCalendarChoice = {
  id: string;
  summary: string;
  primary: boolean;
  access_role: string | null;
};
