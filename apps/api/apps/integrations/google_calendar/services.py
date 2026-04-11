from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.core import signing
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.events.models import Event
from apps.integrations.google_calendar.client import (
    GoogleCalendarApiClient,
    GoogleCalendarError,
    GoogleCalendarNotFoundError,
    GoogleCalendarUnauthorizedError,
)
from apps.integrations.google_calendar.models import GoogleCalendarConnection
from apps.organizations.models import Organization
from apps.organizations.services import get_active_membership_for_org_id
from apps.permissions.services import can_manage_google_calendar

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class OAuthCallbackResult:
    organization_id: str
    redirect_path: str
    success: bool
    error: str | None = None


def get_google_calendar_client() -> GoogleCalendarApiClient:
    return GoogleCalendarApiClient()


def is_google_oauth_configured() -> bool:
    return bool(
        settings.GOOGLE_OAUTH_CLIENT_ID
        and settings.GOOGLE_OAUTH_CLIENT_SECRET
        and settings.GOOGLE_OAUTH_REDIRECT_URI
    )


def get_google_calendar_connection(organization: Organization) -> GoogleCalendarConnection | None:
    return (
        GoogleCalendarConnection.objects.select_related("organization", "connected_by_user")
        .filter(organization=organization)
        .first()
    )


def get_google_calendar_connection_status(organization: Organization) -> dict:
    connection = get_google_calendar_connection(organization)
    return {
        "oauth_configured": is_google_oauth_configured(),
        "connected": connection is not None,
        "google_account_email": connection.google_account_email if connection else None,
        "calendar_id": connection.calendar_id if connection else None,
        "token_expiry": connection.token_expiry if connection else None,
        "last_sync_error": connection.last_sync_error if connection else None,
        "last_sync_error_at": connection.last_sync_error_at if connection else None,
        "last_calendar_sync_at": connection.last_calendar_sync_at if connection else None,
    }


def _require_google_oauth_configured() -> None:
    if is_google_oauth_configured():
        return
    raise ValidationError(
        {
            "google_calendar": [
                "Google OAuth is not configured. Set client ID, secret, and redirect URI."
            ]
        }
    )


def _sign_oauth_state(payload: dict) -> str:
    return signing.dumps(payload, salt="google-calendar-oauth-state")


def _load_oauth_state(state: str) -> dict:
    try:
        return signing.loads(
            state,
            salt="google-calendar-oauth-state",
            max_age=settings.GOOGLE_OAUTH_STATE_TTL_SECONDS,
        )
    except signing.BadSignature as exc:
        raise ValidationError({"state": ["OAuth state is invalid or expired."]}) from exc


def build_google_oauth_authorization_url(organization: Organization, user) -> str:
    _require_google_oauth_configured()
    if not can_manage_google_calendar(user, organization):
        raise PermissionDenied("You cannot manage Google Calendar in this organization.")

    state = _sign_oauth_state(
        {
            "org_id": str(organization.id),
            "user_id": str(user.id),
            "redirect_path": f"/app/{organization.id}/settings/google-calendar",
        }
    )
    return get_google_calendar_client().build_authorization_url(state=state)


def _build_callback_redirect_url(
    *,
    redirect_path: str,
    organization_id: str,
    success: bool,
    detail: str | None = None,
) -> str:
    query = {"google_calendar": "connected" if success else "error"}
    if detail:
        query["detail"] = detail
    return f"{settings.WEB_APP_BASE_URL}{redirect_path}?{urlencode(query)}"


@transaction.atomic
def connect_google_calendar_with_oauth_code(
    *,
    code: str,
    state: str,
    client: GoogleCalendarApiClient | None = None,
) -> OAuthCallbackResult:
    client = client or get_google_calendar_client()
    state_payload = _load_oauth_state(state)

    membership = get_active_membership_for_org_id(
        user=User.objects.get(id=state_payload["user_id"]),
        organization_id=state_payload["org_id"],
    )
    if membership is None or not can_manage_google_calendar(
        membership.user,
        membership.organization,
    ):
        raise PermissionDenied("The original user can no longer manage Google Calendar.")

    tokens = client.exchange_code_for_tokens(code=code)
    google_account_email = client.fetch_user_email(access_token=tokens.access_token)

    connection, _ = GoogleCalendarConnection.objects.get_or_create(
        organization=membership.organization,
        defaults={
            "connected_by_user": membership.user,
            "google_account_email": google_account_email,
            "access_token": "",
            "refresh_token": "",
        },
    )
    connection.connected_by_user = membership.user
    connection.google_account_email = google_account_email
    connection.set_access_token(tokens.access_token)
    if tokens.refresh_token:
        connection.set_refresh_token(tokens.refresh_token)
    elif not connection.refresh_token:
        raise ValidationError(
            {"google_calendar": ["Google did not return a refresh token. Retry consent."]}
        )
    connection.token_expiry = (
        timezone.now() + timedelta(seconds=tokens.expires_in)
        if tokens.expires_in is not None
        else None
    )
    connection.last_sync_error = None
    connection.last_sync_error_at = None
    connection.save()
    return OAuthCallbackResult(
        organization_id=str(membership.organization_id),
        redirect_path=state_payload["redirect_path"],
        success=True,
    )


def handle_google_oauth_callback(
    *,
    code: str | None,
    state: str | None,
    error: str | None = None,
    client: GoogleCalendarApiClient | None = None,
) -> str:
    if not state:
        fallback_path = f"{settings.WEB_APP_BASE_URL}/app"
        return f"{fallback_path}?google_calendar=error&detail=missing_state"

    try:
        state_payload = _load_oauth_state(state)
    except ValidationError:
        fallback_path = f"{settings.WEB_APP_BASE_URL}/app"
        return f"{fallback_path}?google_calendar=error&detail=invalid_state"

    redirect_path = state_payload["redirect_path"]
    organization_id = state_payload["org_id"]

    if error:
        return _build_callback_redirect_url(
            redirect_path=redirect_path,
            organization_id=organization_id,
            success=False,
            detail=error,
        )

    if not code:
        return _build_callback_redirect_url(
            redirect_path=redirect_path,
            organization_id=organization_id,
            success=False,
            detail="missing_code",
        )

    try:
        connect_google_calendar_with_oauth_code(code=code, state=state, client=client)
    except Exception as exc:
        logger.exception("Google OAuth callback failed for organization %s", organization_id)
        return _build_callback_redirect_url(
            redirect_path=redirect_path,
            organization_id=organization_id,
            success=False,
            detail=str(exc),
        )

    return _build_callback_redirect_url(
        redirect_path=redirect_path,
        organization_id=organization_id,
        success=True,
    )


def _record_connection_sync_success(connection: GoogleCalendarConnection) -> None:
    connection.last_sync_error = None
    connection.last_sync_error_at = None
    connection.last_calendar_sync_at = timezone.now()
    connection.save(
        update_fields=[
            "last_sync_error",
            "last_sync_error_at",
            "last_calendar_sync_at",
            "updated_at",
        ]
    )


def _record_connection_sync_failure(connection: GoogleCalendarConnection, message: str) -> None:
    connection.last_sync_error = message
    connection.last_sync_error_at = timezone.now()
    connection.save(update_fields=["last_sync_error", "last_sync_error_at", "updated_at"])


def refresh_google_calendar_access_token(
    connection: GoogleCalendarConnection,
    *,
    client: GoogleCalendarApiClient | None = None,
) -> GoogleCalendarConnection:
    client = client or get_google_calendar_client()
    tokens = client.refresh_access_token(refresh_token=connection.get_refresh_token())
    connection.set_access_token(tokens.access_token)
    if tokens.refresh_token:
        connection.set_refresh_token(tokens.refresh_token)
    connection.token_expiry = (
        timezone.now() + timedelta(seconds=tokens.expires_in)
        if tokens.expires_in is not None
        else None
    )
    connection.save(update_fields=["access_token", "refresh_token", "token_expiry", "updated_at"])
    return connection


def _get_connection_access_token(
    connection: GoogleCalendarConnection,
    *,
    client: GoogleCalendarApiClient | None = None,
    force_refresh: bool = False,
) -> str:
    client = client or get_google_calendar_client()
    if force_refresh or (
        connection.token_expiry is not None
        and connection.token_expiry <= timezone.now() + timedelta(minutes=1)
    ):
        connection = refresh_google_calendar_access_token(connection, client=client)
    return connection.get_access_token()


def list_google_calendars(
    organization: Organization,
    *,
    client: GoogleCalendarApiClient | None = None,
) -> list[dict]:
    connection = get_google_calendar_connection(organization)
    if connection is None:
        raise ValidationError({"google_calendar": ["No Google Calendar connection exists."]})

    client = client or get_google_calendar_client()
    access_token = _get_connection_access_token(connection, client=client)
    try:
        calendars = client.list_calendars(access_token=access_token)
    except GoogleCalendarUnauthorizedError:
        access_token = _get_connection_access_token(connection, client=client, force_refresh=True)
        calendars = client.list_calendars(access_token=access_token)

    return [
        {
            "id": calendar["id"],
            "summary": calendar.get("summary") or calendar["id"],
            "primary": bool(calendar.get("primary")),
            "access_role": calendar.get("accessRole"),
        }
        for calendar in calendars
    ]


def _clear_organization_event_sync_state(organization: Organization) -> None:
    Event.objects.filter(organization=organization).update(
        google_calendar_event_id=None,
        google_calendar_last_synced_at=None,
        google_calendar_sync_error=None,
    )


@transaction.atomic
def select_google_calendar(
    organization: Organization,
    calendar_id: str,
) -> GoogleCalendarConnection:
    connection = get_google_calendar_connection(organization)
    if connection is None:
        raise ValidationError({"google_calendar": ["No Google Calendar connection exists."]})

    available_ids = {calendar["id"] for calendar in list_google_calendars(organization)}
    if calendar_id not in available_ids:
        raise ValidationError(
            {"calendar_id": ["Calendar not found for the connected Google account."]}
        )

    if connection.calendar_id != calendar_id:
        _clear_organization_event_sync_state(organization)
    connection.calendar_id = calendar_id
    connection.save(update_fields=["calendar_id", "updated_at"])
    return connection


@transaction.atomic
def disconnect_google_calendar(
    organization: Organization,
    *,
    client: GoogleCalendarApiClient | None = None,
) -> None:
    connection = get_google_calendar_connection(organization)
    if connection is None:
        return

    client = client or get_google_calendar_client()
    try:
        client.revoke_token(token=connection.get_refresh_token())
    except GoogleCalendarError:
        logger.warning(
            "Failed to revoke Google token for organization %s during disconnect.",
            organization.id,
            exc_info=True,
        )

    _clear_organization_event_sync_state(organization)
    connection.delete()


def get_event_google_calendar_sync_status(event: Event) -> dict:
    if event.google_calendar_sync_error:
        status = "failed"
    elif event.google_calendar_last_synced_at:
        status = "synced"
    elif event.google_calendar_event_id:
        status = "linked"
    else:
        status = "not_synced"
    return {
        "status": status,
        "last_synced_at": event.google_calendar_last_synced_at,
        "error": event.google_calendar_sync_error,
    }


def _build_google_event_payload(event: Event) -> dict:
    if event.is_all_day:
        start_date = event.start_at.date()
        end_date = event.end_at.date()
        if end_date <= start_date:
            end_date = start_date + timedelta(days=1)
        start = {"date": start_date.isoformat()}
        end = {"date": end_date.isoformat()}
    else:
        start = {"dateTime": event.start_at.isoformat(), "timeZone": event.timezone}
        end = {"dateTime": event.end_at.isoformat(), "timeZone": event.timezone}

    return {
        "summary": event.title,
        "description": event.description or "",
        "location": event.location or "",
        "start": start,
        "end": end,
        "extendedProperties": {
            "private": {
                "choir_event_id": str(event.id),
                "choir_organization_id": str(event.organization_id),
            }
        },
    }


def sync_event_to_google_calendar(
    event: Event,
    *,
    client: GoogleCalendarApiClient | None = None,
) -> Event:
    connection = get_google_calendar_connection(event.organization)
    if connection is None or not connection.calendar_id:
        return event

    client = client or get_google_calendar_client()
    payload = _build_google_event_payload(event)

    try:
        access_token = _get_connection_access_token(connection, client=client)
        if event.google_calendar_event_id:
            try:
                google_event = client.update_event(
                    access_token=access_token,
                    calendar_id=connection.calendar_id,
                    google_event_id=event.google_calendar_event_id,
                    payload=payload,
                )
            except GoogleCalendarNotFoundError:
                google_event = client.insert_event(
                    access_token=access_token,
                    calendar_id=connection.calendar_id,
                    payload=payload,
                )
        else:
            google_event = client.insert_event(
                access_token=access_token,
                calendar_id=connection.calendar_id,
                payload=payload,
            )
    except GoogleCalendarUnauthorizedError:
        try:
            access_token = _get_connection_access_token(
                connection,
                client=client,
                force_refresh=True,
            )
            if event.google_calendar_event_id:
                google_event = client.update_event(
                    access_token=access_token,
                    calendar_id=connection.calendar_id,
                    google_event_id=event.google_calendar_event_id,
                    payload=payload,
                )
            else:
                google_event = client.insert_event(
                    access_token=access_token,
                    calendar_id=connection.calendar_id,
                    payload=payload,
                )
        except Exception as exc:
            message = str(exc)
            logger.exception(
                "Google Calendar sync failed for event %s after token refresh.",
                event.id,
            )
            event.google_calendar_sync_error = message
            event.save(update_fields=["google_calendar_sync_error", "updated_at"])
            _record_connection_sync_failure(connection, message)
            return event
    except Exception as exc:
        message = str(exc)
        logger.exception("Google Calendar sync failed for event %s.", event.id)
        event.google_calendar_sync_error = message
        event.save(update_fields=["google_calendar_sync_error", "updated_at"])
        _record_connection_sync_failure(connection, message)
        return event

    event.google_calendar_event_id = google_event["id"]
    event.google_calendar_last_synced_at = timezone.now()
    event.google_calendar_sync_error = None
    event.save(
        update_fields=[
            "google_calendar_event_id",
            "google_calendar_last_synced_at",
            "google_calendar_sync_error",
            "updated_at",
        ]
    )
    _record_connection_sync_success(connection)
    return event


def sync_deleted_event_to_google_calendar(
    *,
    organization: Organization,
    google_calendar_event_id: str | None,
    client: GoogleCalendarApiClient | None = None,
) -> None:
    if not google_calendar_event_id:
        return

    connection = get_google_calendar_connection(organization)
    if connection is None or not connection.calendar_id:
        return

    client = client or get_google_calendar_client()

    try:
        access_token = _get_connection_access_token(connection, client=client)
        client.delete_event(
            access_token=access_token,
            calendar_id=connection.calendar_id,
            google_event_id=google_calendar_event_id,
        )
    except GoogleCalendarUnauthorizedError:
        try:
            access_token = _get_connection_access_token(
                connection,
                client=client,
                force_refresh=True,
            )
            client.delete_event(
                access_token=access_token,
                calendar_id=connection.calendar_id,
                google_event_id=google_calendar_event_id,
            )
        except GoogleCalendarNotFoundError:
            _record_connection_sync_success(connection)
        except Exception as exc:
            logger.exception(
                "Google Calendar delete sync failed for organization %s.",
                organization.id,
            )
            _record_connection_sync_failure(connection, str(exc))
    except GoogleCalendarNotFoundError:
        _record_connection_sync_success(connection)
    except Exception as exc:
        logger.exception(
            "Google Calendar delete sync failed for organization %s.",
            organization.id,
        )
        _record_connection_sync_failure(connection, str(exc))
    else:
        _record_connection_sync_success(connection)
