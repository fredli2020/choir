from django.conf import settings
from django.db import models

from apps.core.models import UUIDTimeStampedModel
from apps.integrations.google_calendar.crypto import decrypt_token, encrypt_token
from apps.organizations.models import Organization


class GoogleCalendarConnection(UUIDTimeStampedModel):
    organization = models.OneToOneField(
        Organization,
        on_delete=models.CASCADE,
        related_name="google_calendar_connection",
    )
    connected_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="google_calendar_connections",
    )
    google_account_email = models.EmailField()
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField(null=True, blank=True)
    calendar_id = models.CharField(max_length=255, null=True, blank=True)
    last_sync_error = models.TextField(null=True, blank=True)
    last_sync_error_at = models.DateTimeField(null=True, blank=True)
    last_calendar_sync_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["organization__name"]

    def __str__(self) -> str:
        return f"{self.organization} Google Calendar"

    def set_access_token(self, raw_value: str) -> None:
        self.access_token = encrypt_token(raw_value)

    def get_access_token(self) -> str:
        return decrypt_token(self.access_token)

    def set_refresh_token(self, raw_value: str) -> None:
        self.refresh_token = encrypt_token(raw_value)

    def get_refresh_token(self) -> str:
        return decrypt_token(self.refresh_token)
