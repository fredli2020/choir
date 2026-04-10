from django.urls import path

from apps.events.views import (
    AttendanceRosterView,
    EventAudienceView,
    EventDetailView,
    EventListCreateView,
    EventRSVPListView,
    MyEventResponsesView,
    MyRSVPView,
    RelevantEventListView,
    UpcomingRelevantEventListView,
)

urlpatterns = [
    path("orgs/<uuid:org_id>/events", EventListCreateView.as_view(), name="event-list"),
    path(
        "orgs/<uuid:org_id>/events/relevant",
        RelevantEventListView.as_view(),
        name="event-relevant-list",
    ),
    path(
        "orgs/<uuid:org_id>/events/upcoming",
        UpcomingRelevantEventListView.as_view(),
        name="event-upcoming-list",
    ),
    path(
        "orgs/<uuid:org_id>/events/my-responses",
        MyEventResponsesView.as_view(),
        name="event-my-responses",
    ),
    path(
        "orgs/<uuid:org_id>/events/<uuid:event_id>/audience",
        EventAudienceView.as_view(),
        name="event-audience",
    ),
    path(
        "orgs/<uuid:org_id>/events/<uuid:event_id>/my-rsvp",
        MyRSVPView.as_view(),
        name="event-my-rsvp",
    ),
    path(
        "orgs/<uuid:org_id>/events/<uuid:event_id>/rsvps",
        EventRSVPListView.as_view(),
        name="event-rsvps",
    ),
    path(
        "orgs/<uuid:org_id>/events/<uuid:event_id>/attendance",
        AttendanceRosterView.as_view(),
        name="event-attendance",
    ),
    path(
        "orgs/<uuid:org_id>/events/<uuid:event_id>",
        EventDetailView.as_view(),
        name="event-detail",
    ),
]
