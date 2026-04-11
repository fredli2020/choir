from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from django.utils import timezone

from apps.events.models import Event, EventAudience
from apps.integrations.google_calendar.client import OAuthTokens
from apps.integrations.google_calendar.models import GoogleCalendarConnection
from apps.integrations.google_calendar.services import (
    build_google_oauth_authorization_url,
    connect_google_calendar_with_oauth_code,
    handle_google_oauth_callback,
    list_google_calendars,
)


class FakeGoogleCalendarClient:
    def __init__(self):
        self.refreshed = False

    def build_authorization_url(self, *, state: str) -> str:
        return f"https://accounts.google.com/o/oauth2/v2/auth?client_id=test-client&state={state}"

    def exchange_code_for_tokens(self, *, code: str) -> OAuthTokens:
        assert code == "oauth-code"
        return OAuthTokens(
            access_token="access-token",
            refresh_token="refresh-token",
            expires_in=3600,
        )

    def fetch_user_email(self, *, access_token: str) -> str:
        assert access_token == "access-token"
        return "calendar-admin@example.com"

    def refresh_access_token(self, *, refresh_token: str) -> OAuthTokens:
        assert refresh_token == "refresh-token"
        self.refreshed = True
        return OAuthTokens(
            access_token="refreshed-access-token",
            refresh_token=None,
            expires_in=3600,
        )

    def list_calendars(self, *, access_token: str) -> list[dict]:
        assert access_token == "refreshed-access-token"
        return [
            {
                "id": "primary",
                "summary": "Primary Choir Calendar",
                "primary": True,
                "accessRole": "owner",
            }
        ]

    def insert_event(self, *, access_token: str, calendar_id: str, payload: dict) -> dict:
        return {"id": "google-event-123"}

    def update_event(
        self,
        *,
        access_token: str,
        calendar_id: str,
        google_event_id: str,
        payload: dict,
    ) -> dict:
        return {"id": google_event_id}

    def delete_event(self, *, access_token: str, calendar_id: str, google_event_id: str) -> None:
        return None

    def revoke_token(self, *, token: str) -> None:
        return None


class FailingGoogleCalendarClient(FakeGoogleCalendarClient):
    def insert_event(self, *, access_token: str, calendar_id: str, payload: dict) -> dict:
        raise RuntimeError("Google Calendar insert failed.")


@pytest.mark.django_db
def test_build_google_oauth_authorization_url_contains_signed_state(
    organization,
    admin_user,
    admin_membership,
):
    authorization_url = build_google_oauth_authorization_url(organization, admin_user)

    parsed = urlparse(authorization_url)
    query = parse_qs(parsed.query)

    assert parsed.netloc == "accounts.google.com"
    assert query["client_id"] == ["google-client-id"]
    assert "state" in query


@pytest.mark.django_db
def test_oauth_callback_persists_encrypted_tokens_and_can_refresh_calendar_list(
    organization,
    admin_user,
    admin_membership,
):
    fake_client = FakeGoogleCalendarClient()
    authorization_url = build_google_oauth_authorization_url(organization, admin_user)
    state = parse_qs(urlparse(authorization_url).query)["state"][0]

    result = connect_google_calendar_with_oauth_code(
        code="oauth-code",
        state=state,
        client=fake_client,
    )

    connection = GoogleCalendarConnection.objects.get(organization=organization)
    assert result.success is True
    assert connection.google_account_email == "calendar-admin@example.com"
    assert connection.access_token != "access-token"
    assert connection.get_access_token() == "access-token"
    assert connection.get_refresh_token() == "refresh-token"

    connection.token_expiry = timezone.now() - timedelta(minutes=5)
    connection.calendar_id = "primary"
    connection.save(update_fields=["token_expiry", "calendar_id", "updated_at"])

    calendars = list_google_calendars(organization, client=fake_client)

    assert fake_client.refreshed is True
    assert calendars == [
        {
            "id": "primary",
            "summary": "Primary Choir Calendar",
            "primary": True,
            "access_role": "owner",
        }
    ]


@pytest.mark.django_db
def test_member_cannot_access_google_calendar_status(api_client, member_user, member_membership):
    api_client.force_authenticate(user=member_user)

    response = api_client.get(
        f"/api/orgs/{member_membership.organization_id}/integrations/google-calendar"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_google_oauth_callback_with_invalid_state_redirects_to_safe_error():
    redirect_url = handle_google_oauth_callback(code="oauth-code", state="invalid-state")

    parsed = urlparse(redirect_url)
    query = parse_qs(parsed.query)

    assert parsed.path == "/app"
    assert query["google_calendar"] == ["error"]
    assert query["detail"] == ["invalid_state"]


@pytest.mark.django_db
def test_event_create_syncs_to_google_calendar_when_connection_is_selected(
    api_client,
    admin_user,
    admin_membership,
    monkeypatch,
    now,
):
    connection = GoogleCalendarConnection.objects.create(
        organization=admin_membership.organization,
        connected_by_user=admin_user,
        google_account_email="calendar-admin@example.com",
        access_token="",
        refresh_token="",
        token_expiry=timezone.now() + timedelta(hours=1),
        calendar_id="primary",
    )
    connection.set_access_token("access-token")
    connection.set_refresh_token("refresh-token")
    connection.save(update_fields=["access_token", "refresh_token", "updated_at"])

    monkeypatch.setattr(
        "apps.integrations.google_calendar.services.get_google_calendar_client",
        lambda: FakeGoogleCalendarClient(),
    )

    api_client.force_authenticate(user=admin_user)
    response = api_client.post(
        f"/api/orgs/{admin_membership.organization_id}/events",
        {
            "title": "Synced Rehearsal",
            "description": "Push to Google Calendar",
            "type": Event.Type.REHEARSAL,
            "location": "Choir Room",
            "start_at": now.isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "America/New_York",
            "is_all_day": False,
            "audience": {"audience_type": EventAudience.AudienceType.ALL_MEMBERS},
        },
        format="json",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["google_calendar_event_id"] == "google-event-123"
    assert payload["google_calendar_sync"]["status"] == "synced"


@pytest.mark.django_db
def test_event_create_preserves_local_data_when_google_sync_fails(
    api_client,
    admin_user,
    admin_membership,
    monkeypatch,
    now,
):
    connection = GoogleCalendarConnection.objects.create(
        organization=admin_membership.organization,
        connected_by_user=admin_user,
        google_account_email="calendar-admin@example.com",
        access_token="",
        refresh_token="",
        token_expiry=timezone.now() + timedelta(hours=1),
        calendar_id="primary",
    )
    connection.set_access_token("access-token")
    connection.set_refresh_token("refresh-token")
    connection.save(update_fields=["access_token", "refresh_token", "updated_at"])

    monkeypatch.setattr(
        "apps.integrations.google_calendar.services.get_google_calendar_client",
        lambda: FailingGoogleCalendarClient(),
    )

    api_client.force_authenticate(user=admin_user)
    response = api_client.post(
        f"/api/orgs/{admin_membership.organization_id}/events",
        {
            "title": "Locally Saved Event",
            "description": "Google will fail",
            "type": Event.Type.MEETING,
            "location": "Music Office",
            "start_at": now.isoformat(),
            "end_at": (now + timedelta(hours=1)).isoformat(),
            "timezone": "America/New_York",
            "is_all_day": False,
            "audience": {"audience_type": EventAudience.AudienceType.ALL_MEMBERS},
        },
        format="json",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["google_calendar_event_id"] is None
    assert payload["google_calendar_sync"]["status"] == "failed"
    assert "Google Calendar insert failed." in payload["google_calendar_sync"]["error"]
    assert Event.objects.filter(
        organization=admin_membership.organization,
        title="Locally Saved Event",
    ).exists()
