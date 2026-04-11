from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, request

from django.conf import settings


class EmailProviderError(Exception):
    pass


@dataclass(slots=True)
class EmailSendResult:
    provider_message_id: str | None = None


class BaseEmailProvider:
    def send_email(self, *, to_email: str, subject: str, body: str) -> EmailSendResult:
        raise NotImplementedError


class ResendEmailProvider(BaseEmailProvider):
    api_url = "https://api.resend.com/emails"

    def __init__(self, *, api_key: str, from_email: str):
        self.api_key = api_key
        self.from_email = from_email

    def send_email(self, *, to_email: str, subject: str, body: str) -> EmailSendResult:
        payload = json.dumps(
            {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "text": body,
            }
        ).encode("utf-8")
        req = request.Request(
            self.api_url,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=10) as response:
                raw_body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            raise EmailProviderError(
                f"Resend returned HTTP {exc.code}: {response_body[:500]}"
            ) from exc
        except error.URLError as exc:
            raise EmailProviderError(f"Resend request failed: {exc.reason}") from exc

        data = json.loads(raw_body or "{}")
        return EmailSendResult(provider_message_id=data.get("id"))


def get_email_provider() -> BaseEmailProvider:
    provider_name = settings.COMMUNICATIONS_EMAIL_PROVIDER
    if provider_name == "resend":
        if not settings.RESEND_API_KEY:
            raise EmailProviderError(
                "RESEND_API_KEY must be configured to send message campaigns."
            )
        return ResendEmailProvider(
            api_key=settings.RESEND_API_KEY,
            from_email=settings.DEFAULT_FROM_EMAIL,
        )

    raise EmailProviderError(f"Unsupported email provider: {provider_name}")

