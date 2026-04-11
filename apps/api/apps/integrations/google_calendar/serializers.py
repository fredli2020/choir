from rest_framework import serializers

from apps.integrations.google_calendar.models import GoogleCalendarConnection


class GoogleCalendarConnectionStatusSerializer(serializers.Serializer):
    oauth_configured = serializers.BooleanField()
    connected = serializers.BooleanField()
    google_account_email = serializers.CharField(allow_null=True)
    calendar_id = serializers.CharField(allow_null=True)
    token_expiry = serializers.DateTimeField(allow_null=True)
    last_sync_error = serializers.CharField(allow_null=True)
    last_sync_error_at = serializers.DateTimeField(allow_null=True)
    last_calendar_sync_at = serializers.DateTimeField(allow_null=True)


class GoogleCalendarOAuthStartSerializer(serializers.Serializer):
    authorization_url = serializers.URLField()


class GoogleCalendarChoiceSerializer(serializers.Serializer):
    id = serializers.CharField()
    summary = serializers.CharField()
    primary = serializers.BooleanField()
    access_role = serializers.CharField(allow_null=True)


class GoogleCalendarListSerializer(serializers.Serializer):
    calendars = GoogleCalendarChoiceSerializer(many=True)


class GoogleCalendarSelectionSerializer(serializers.Serializer):
    calendar_id = serializers.CharField(max_length=255)


class GoogleCalendarConnectionReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoogleCalendarConnection
        fields = [
            "id",
            "organization_id",
            "connected_by_user_id",
            "google_account_email",
            "token_expiry",
            "calendar_id",
            "last_sync_error",
            "last_sync_error_at",
            "last_calendar_sync_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
