# Roadmap

## Core modules planned later

- Organizations and memberships
- Authentication and roles
- People roster
- Events and attendance
- Google Calendar sync integration
- Messaging and notifications
- Reporting and exports

## Explicitly deferred for now

- Payments
- Ticketing
- Music library
- Donor CRM
- Parent/child accounts
- Public event pages

## Future extension points

- Payments: add billing, dues tracking, or paid-event flows without mixing finance logic into current membership and event modules.
- Ticketing: add public or internal ticket workflows on top of events without changing the current event source-of-truth model.
- Music library: introduce repertoire, files, planning, and permissions as a separate domain module instead of overloading events.
- Parent/child accounts: extend identity and membership linking for youth programs while keeping `User` and `MemberProfile` distinct.
- Public event pages: add a public-facing read model and routing layer rather than weakening the current authenticated org API boundary.
