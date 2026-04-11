from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, parse, request

from django.conf import settings


class GoogleCalendarError(Exception):
    pass


class GoogleCalendarUnauthorizedError(GoogleCalendarError):
    pass


class GoogleCalendarNotFoundError(GoogleCalendarError):
    pass


@dataclass(slots=True)
class OAuthTokens:
    access_token: str
    refresh_token: str | None
    expires_in: int | None


class GoogleCalendarApiClient:
    auth_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url = "https://oauth2.googleapis.com/token"
    revoke_url = "https://oauth2.googleapis.com/revoke"
    userinfo_url = "https://openidconnect.googleapis.com/v1/userinfo"
    calendar_list_url = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
    calendar_events_base_url = "https://www.googleapis.com/calendar/v3/calendars"

    def build_authorization_url(self, *, state: str) -> str:
        query = parse.urlencode(
            {
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
                "response_type": "code",
                "scope": " ".join(settings.GOOGLE_OAUTH_SCOPES),
                "access_type": "offline",
                "prompt": "consent",
                "include_granted_scopes": "true",
                "state": state,
            }
        )
        return f"{self.auth_base_url}?{query}"

    def exchange_code_for_tokens(self, *, code: str) -> OAuthTokens:
        payload = self._post_form(
            self.token_url,
            {
                "code": code,
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        return OAuthTokens(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            expires_in=payload.get("expires_in"),
        )

    def refresh_access_token(self, *, refresh_token: str) -> OAuthTokens:
        payload = self._post_form(
            self.token_url,
            {
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        return OAuthTokens(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            expires_in=payload.get("expires_in"),
        )

    def revoke_token(self, *, token: str) -> None:
        encoded = parse.urlencode({"token": token}).encode("utf-8")
        req = request.Request(
            self.revoke_url,
            data=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=10):
                return
        except error.HTTPError as exc:
            raise GoogleCalendarError(
                f"Google token revocation failed with HTTP {exc.code}."
            ) from exc
        except error.URLError as exc:
            raise GoogleCalendarError(f"Google token revocation failed: {exc.reason}") from exc

    def fetch_user_email(self, *, access_token: str) -> str:
        payload = self._request_json(
            self.userinfo_url,
            method="GET",
            access_token=access_token,
        )
        email = payload.get("email")
        if not email:
            raise GoogleCalendarError("Google did not return an account email.")
        return email

    def list_calendars(self, *, access_token: str) -> list[dict]:
        payload = self._request_json(
            self.calendar_list_url,
            method="GET",
            access_token=access_token,
        )
        return payload.get("items", [])

    def insert_event(self, *, access_token: str, calendar_id: str, payload: dict) -> dict:
        url = f"{self.calendar_events_base_url}/{parse.quote(calendar_id, safe='')}/events"
        return self._request_json(url, method="POST", access_token=access_token, json_body=payload)

    def update_event(
        self,
        *,
        access_token: str,
        calendar_id: str,
        google_event_id: str,
        payload: dict,
    ) -> dict:
        url = (
            f"{self.calendar_events_base_url}/{parse.quote(calendar_id, safe='')}/events/"
            f"{parse.quote(google_event_id, safe='')}"
        )
        return self._request_json(url, method="PATCH", access_token=access_token, json_body=payload)

    def delete_event(self, *, access_token: str, calendar_id: str, google_event_id: str) -> None:
        url = (
            f"{self.calendar_events_base_url}/{parse.quote(calendar_id, safe='')}/events/"
            f"{parse.quote(google_event_id, safe='')}"
        )
        self._request_json(url, method="DELETE", access_token=access_token, allow_empty=True)

    def _post_form(self, url: str, data: dict) -> dict:
        encoded = parse.urlencode(data).encode("utf-8")
        req = request.Request(
            url,
            data=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=10) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise GoogleCalendarError(
                f"Google OAuth request failed with HTTP {exc.code}: {body[:500]}"
            ) from exc
        except error.URLError as exc:
            raise GoogleCalendarError(f"Google OAuth request failed: {exc.reason}") from exc
        return json.loads(raw_body or "{}")

    def _request_json(
        self,
        url: str,
        *,
        method: str,
        access_token: str,
        json_body: dict | None = None,
        allow_empty: bool = False,
    ) -> dict:
        payload = json.dumps(json_body).encode("utf-8") if json_body is not None else None
        headers = {"Authorization": f"Bearer {access_token}"}
        if json_body is not None:
            headers["Content-Type"] = "application/json"
        req = request.Request(url, data=payload, headers=headers, method=method)
        try:
            with request.urlopen(req, timeout=10) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            if exc.code == 401:
                raise GoogleCalendarUnauthorizedError(
                    "Google access token expired or was rejected."
                ) from exc
            if exc.code == 404:
                raise GoogleCalendarNotFoundError(
                    "Google calendar resource was not found."
                ) from exc
            body = exc.read().decode("utf-8", errors="replace")
            raise GoogleCalendarError(
                f"Google Calendar API failed with HTTP {exc.code}: {body[:500]}"
            ) from exc
        except error.URLError as exc:
            raise GoogleCalendarError(f"Google Calendar API request failed: {exc.reason}") from exc

        if allow_empty and not raw_body:
            return {}
        return json.loads(raw_body or "{}")
