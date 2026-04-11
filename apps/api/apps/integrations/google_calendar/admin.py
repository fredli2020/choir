from django.contrib import admin

from apps.integrations.google_calendar.models import GoogleCalendarConnection


@admin.register(GoogleCalendarConnection)
class GoogleCalendarConnectionAdmin(admin.ModelAdmin):
    list_display = [
        "organization",
        "google_account_email",
        "calendar_id",
        "last_calendar_sync_at",
    ]
    search_fields = ["organization__name", "google_account_email", "calendar_id"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "last_calendar_sync_at",
        "last_sync_error_at",
    ]

