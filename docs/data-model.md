# Data Model

## Core Identity And Org Models

### User

- Login identity synced from Clerk

### Organization

- Top-level org container

### OrganizationMembership

- Links a `User` to an `Organization`
- Roles: `admin`, `section_leader`, `member`

## Member Models

### MemberProfile

- Org-scoped member record
- Optional link to `User`
- Source of member-facing roster, directory, and group membership

### Group

- Org-scoped named group
- Types: `section`, `committee`, `ensemble`, `other`

### GroupMember

- Join model between `Group` and `MemberProfile`

## Event Models

### Event

- Core scheduling record
- Source of truth for all calendar behavior
- Stores optional Google sync fields:
  - `google_calendar_event_id`
  - `google_calendar_last_synced_at`
  - `google_calendar_sync_error`

### EventAudience

- Audience rows for:
  - `all_members`
  - `group`
  - `selected_members`

### RSVP

- Per-member response to an event

### AttendanceRecord

- Per-member attendance status for an event

## Communications Models

### Announcement

- In-app announcement
- Can be draft or published

### AnnouncementAudience

- Audience rows for:
  - `all_members`
  - `group`
  - `selected_members`

### MessageCampaign

- Outbound email campaign
- Statuses: `draft`, `sending`, `sent`, `failed`

### MessageRecipient

- Materialized recipient rows for a campaign
- Delivery statuses: `pending`, `sent`, `failed`

## Integration Models

### GoogleCalendarConnection

- One connection per organization
- Stores:
  - connected Google account email
  - encrypted access token
  - encrypted refresh token
  - token expiry
  - selected calendar ID
  - last sync timestamps and error state

## Relationship Summary

- `Organization` has many `OrganizationMembership`
- `Organization` has many `MemberProfile`
- `Organization` has many `Group`
- `Organization` has many `Event`
- `Organization` has many `Announcement`
- `Organization` has many `MessageCampaign`
- `Organization` has one optional `GoogleCalendarConnection`
- `Group` has many `GroupMember`
- `Event` has many `EventAudience`, `RSVP`, and `AttendanceRecord`
- `Announcement` has many `AnnouncementAudience`
- `MessageCampaign` has many `MessageRecipient`

## Source Of Truth Rules

- Local Django models are authoritative.
- Google Calendar is a mirrored outbound integration only.
- Email campaigns persist recipient and delivery results locally.

