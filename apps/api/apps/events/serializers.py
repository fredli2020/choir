from rest_framework import serializers

from apps.events.models import RSVP, AttendanceRecord, Event, EventAudience
from apps.events.services import (
    get_event_attendance_summary,
    get_event_audience_summary,
    get_event_rsvp_summary,
    get_linked_active_member_profile,
    get_member_event_rsvp,
)
from apps.integrations.google_calendar.services import get_event_google_calendar_sync_status
from apps.members.models import Group, MemberProfile


class GroupAudienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ["id", "type", "name"]
        read_only_fields = fields


class MemberProfileSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberProfile
        fields = ["id", "first_name", "last_name", "email", "voice_part", "status"]
        read_only_fields = fields


class EventAudienceWriteSerializer(serializers.Serializer):
    audience_type = serializers.ChoiceField(choices=EventAudience.AudienceType.choices)
    group_id = serializers.UUIDField(required=False, allow_null=True)
    member_profile_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )


class EventWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    type = serializers.ChoiceField(choices=Event.Type.choices)
    location = serializers.CharField(
        max_length=255, required=False, allow_blank=True, allow_null=True
    )
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    timezone = serializers.CharField(max_length=64)
    is_all_day = serializers.BooleanField(required=False)
    google_calendar_event_id = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    audience = EventAudienceWriteSerializer()


class EventAudienceSummarySerializer(serializers.Serializer):
    audience_type = serializers.CharField(allow_null=True)
    group = GroupAudienceSerializer(allow_null=True)
    selected_members = MemberProfileSummarySerializer(many=True)
    member_count = serializers.IntegerField()


class EventRSVPSummarySerializer(serializers.Serializer):
    yes = serializers.IntegerField()
    no = serializers.IntegerField()
    maybe = serializers.IntegerField()
    no_response = serializers.IntegerField()
    total_targeted = serializers.IntegerField()


class EventAttendanceSummarySerializer(serializers.Serializer):
    present = serializers.IntegerField()
    absent = serializers.IntegerField()
    late = serializers.IntegerField()
    excused = serializers.IntegerField()
    total_recorded = serializers.IntegerField()
    total_targeted = serializers.IntegerField()


class RSVPReadSerializer(serializers.ModelSerializer):
    member_profile = MemberProfileSummarySerializer(read_only=True)

    class Meta:
        model = RSVP
        fields = [
            "id",
            "member_profile",
            "status",
            "note",
            "responded_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CurrentMemberRSVPSerializer(serializers.Serializer):
    status = serializers.CharField()
    note = serializers.CharField(allow_null=True)
    responded_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)


class EventReadSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(read_only=True)
    created_by_user_id = serializers.UUIDField(allow_null=True, read_only=True)
    audience = serializers.SerializerMethodField()
    rsvp_summary = serializers.SerializerMethodField()
    attendance_summary = serializers.SerializerMethodField()
    my_rsvp = serializers.SerializerMethodField()
    google_calendar_sync = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            "id",
            "organization_id",
            "title",
            "description",
            "type",
            "location",
            "start_at",
            "end_at",
            "timezone",
            "is_all_day",
            "google_calendar_event_id",
            "google_calendar_sync",
            "created_by_user_id",
            "audience",
            "rsvp_summary",
            "attendance_summary",
            "my_rsvp",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_audience(self, obj):
        return EventAudienceSummarySerializer(get_event_audience_summary(obj)).data

    def get_rsvp_summary(self, obj):
        return EventRSVPSummarySerializer(get_event_rsvp_summary(obj)).data

    def get_attendance_summary(self, obj):
        return EventAttendanceSummarySerializer(get_event_attendance_summary(obj)).data

    def get_my_rsvp(self, obj):
        request = self.context.get("request")
        if request is None:
            return None
        member_profile = get_linked_active_member_profile(obj.organization, request.user)
        rsvp = get_member_event_rsvp(obj, member_profile)
        if rsvp is None:
            return CurrentMemberRSVPSerializer(
                {
                    "status": RSVP.Status.NO_RESPONSE,
                    "note": None,
                    "responded_at": None,
                    "updated_at": None,
                }
            ).data
        return CurrentMemberRSVPSerializer(
            {
                "status": rsvp.status,
                "note": rsvp.note,
                "responded_at": rsvp.responded_at,
                "updated_at": rsvp.updated_at,
            }
        ).data

    def get_google_calendar_sync(self, obj):
        return get_event_google_calendar_sync_status(obj)


class RSVPUpsertSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=RSVP.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class EventRSVPRowSerializer(serializers.Serializer):
    member_profile = MemberProfileSummarySerializer()
    status = serializers.ChoiceField(choices=RSVP.Status.choices)
    note = serializers.CharField(allow_null=True)
    responded_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)


class EventRSVPListSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    summary = EventRSVPSummarySerializer()
    responses = EventRSVPRowSerializer(many=True)


class AttendanceUpdateItemSerializer(serializers.Serializer):
    member_profile_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=AttendanceRecord.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class AttendanceBulkUpdateSerializer(serializers.Serializer):
    records = AttendanceUpdateItemSerializer(many=True)


class AttendanceRosterRowSerializer(serializers.Serializer):
    member_profile = MemberProfileSummarySerializer()
    rsvp_status = serializers.ChoiceField(choices=RSVP.Status.choices)
    rsvp_note = serializers.CharField(allow_null=True)
    attendance_status = serializers.ChoiceField(
        choices=AttendanceRecord.Status.choices,
        allow_null=True,
    )
    attendance_note = serializers.CharField(allow_null=True)
    recorded_at = serializers.DateTimeField(allow_null=True)
    recorded_by_user_id = serializers.UUIDField(allow_null=True)


class AttendanceRosterSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    summary = EventAttendanceSummarySerializer()
    roster = AttendanceRosterRowSerializer(many=True)


class MyEventResponseSerializer(serializers.Serializer):
    event = EventReadSerializer()
    status = serializers.ChoiceField(choices=RSVP.Status.choices)
    note = serializers.CharField(allow_null=True)
    responded_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)
