from django.urls import path

from apps.integrations.google_calendar.views import (
    GoogleCalendarCalendarsView,
    GoogleCalendarConnectionStatusView,
    GoogleCalendarDisconnectView,
    GoogleCalendarOAuthCallbackView,
    GoogleCalendarOAuthStartView,
    GoogleCalendarSelectionView,
)

urlpatterns = [
    path(
        "orgs/<uuid:org_id>/integrations/google-calendar",
        GoogleCalendarConnectionStatusView.as_view(),
        name="google-calendar-status",
    ),
    path(
        "orgs/<uuid:org_id>/integrations/google-calendar/oauth/start",
        GoogleCalendarOAuthStartView.as_view(),
        name="google-calendar-oauth-start",
    ),
    path(
        "integrations/google-calendar/oauth/callback",
        GoogleCalendarOAuthCallbackView.as_view(),
        name="google-calendar-oauth-callback",
    ),
    path(
        "orgs/<uuid:org_id>/integrations/google-calendar/calendars",
        GoogleCalendarCalendarsView.as_view(),
        name="google-calendar-calendars",
    ),
    path(
        "orgs/<uuid:org_id>/integrations/google-calendar/calendar",
        GoogleCalendarSelectionView.as_view(),
        name="google-calendar-select-calendar",
    ),
    path(
        "orgs/<uuid:org_id>/integrations/google-calendar/disconnect",
        GoogleCalendarDisconnectView.as_view(),
        name="google-calendar-disconnect",
    ),
]

