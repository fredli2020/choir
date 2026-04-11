from django.apps import AppConfig


class GoogleCalendarConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.integrations.google_calendar"
    label = "google_calendar"

