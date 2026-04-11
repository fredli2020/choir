# API Overview

## Base URL

All backend routes are served under `/api`.

## Auth

Protected endpoints expect:

```http
Authorization: Bearer <clerk-jwt>
```

Most organization-scoped routes require active membership in the target organization.

## Health

- `GET /api/health/live`
- `GET /api/health/ready`

## Current User

- `GET /api/me`
- `GET /api/me/organizations`
- `GET /api/me/context?organization_id=<uuid>`

## Organization Context

- `GET /api/orgs/<org_id>/membership`
- `GET /api/orgs/<org_id>/permissions`

## Members And Groups

- `GET/POST /api/orgs/<org_id>/members`
- `GET/PATCH/DELETE /api/orgs/<org_id>/members/<member_id>`
- `GET /api/orgs/<org_id>/directory`
- `GET/PATCH /api/orgs/<org_id>/my-profile`
- `GET/POST /api/orgs/<org_id>/groups`
- `GET/PATCH/DELETE /api/orgs/<org_id>/groups/<group_id>`
- `POST /api/orgs/<org_id>/groups/<group_id>/members`
- `DELETE /api/orgs/<org_id>/groups/<group_id>/members/<member_id>`

## Events, RSVPs, Attendance

- `GET/POST /api/orgs/<org_id>/events`
- `GET /api/orgs/<org_id>/events/relevant`
- `GET /api/orgs/<org_id>/events/upcoming`
- `GET /api/orgs/<org_id>/events/my-responses`
- `GET/PATCH/DELETE /api/orgs/<org_id>/events/<event_id>`
- `GET/PUT /api/orgs/<org_id>/events/<event_id>/audience`
- `GET/PUT /api/orgs/<org_id>/events/<event_id>/my-rsvp`
- `GET /api/orgs/<org_id>/events/<event_id>/rsvps`
- `GET/PUT /api/orgs/<org_id>/events/<event_id>/attendance`

## Communications

### Announcements

- `GET/POST /api/orgs/<org_id>/announcements`
- `GET/PATCH /api/orgs/<org_id>/announcements/<announcement_id>`
- `GET/PUT /api/orgs/<org_id>/announcements/<announcement_id>/audience`
- `POST /api/orgs/<org_id>/announcements/<announcement_id>/publish`
- `GET /api/orgs/<org_id>/announcements/feed`
- `GET /api/orgs/<org_id>/announcements/feed/<announcement_id>`

### Campaigns

- `GET/POST /api/orgs/<org_id>/campaigns`
- `GET/PATCH /api/orgs/<org_id>/campaigns/<campaign_id>`
- `GET/PUT /api/orgs/<org_id>/campaigns/<campaign_id>/audience`
- `POST /api/orgs/<org_id>/campaigns/<campaign_id>/send`
- `GET /api/orgs/<org_id>/campaigns/<campaign_id>/results`

## Google Calendar Integration

- `GET /api/orgs/<org_id>/integrations/google-calendar`
- `GET /api/orgs/<org_id>/integrations/google-calendar/oauth/start`
- `GET /api/integrations/google-calendar/oauth/callback`
- `GET /api/orgs/<org_id>/integrations/google-calendar/calendars`
- `PUT /api/orgs/<org_id>/integrations/google-calendar/calendar`
- `DELETE /api/orgs/<org_id>/integrations/google-calendar/disconnect`

## Notes

- Local app data is the source of truth.
- Email campaigns are plain-text and sent through a provider abstraction.
- Google Calendar sync is one-way from local events to Google Calendar.

