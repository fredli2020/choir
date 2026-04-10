from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.core.models import UUIDModel, UUIDTimeStampedModel
from apps.members.models import Group, MemberProfile
from apps.organizations.models import Organization


class Event(UUIDTimeStampedModel):
    class Type(models.TextChoices):
        REHEARSAL = "rehearsal", "Rehearsal"
        PERFORMANCE = "performance", "Performance"
        MEETING = "meeting", "Meeting"
        OTHER = "other", "Other"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="events",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=32, choices=Type.choices)
    location = models.CharField(max_length=255, null=True, blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    timezone = models.CharField(max_length=64)
    is_all_day = models.BooleanField(default=False)
    google_calendar_event_id = models.CharField(max_length=255, null=True, blank=True)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_events",
    )

    class Meta:
        ordering = ["start_at", "title"]
        indexes = [
            models.Index(fields=["organization", "start_at"], name="event_org_start_idx"),
            models.Index(
                fields=["organization", "type", "start_at"],
                name="event_org_type_start_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.title


class EventAudience(UUIDModel):
    class AudienceType(models.TextChoices):
        ALL_MEMBERS = "all_members", "All members"
        GROUP = "group", "Group"
        SELECTED_MEMBERS = "selected_members", "Selected members"

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="audiences",
    )
    audience_type = models.CharField(max_length=32, choices=AudienceType.choices)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="event_audiences",
    )
    member_profile = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="event_audiences",
    )

    class Meta:
        indexes = [
            models.Index(fields=["event", "audience_type"], name="event_audience_type_idx"),
            models.Index(fields=["group"], name="event_audience_group_idx"),
            models.Index(fields=["member_profile"], name="event_audience_member_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(
                        audience_type="all_members",
                        group__isnull=True,
                        member_profile__isnull=True,
                    )
                    | Q(
                        audience_type="group",
                        group__isnull=False,
                        member_profile__isnull=True,
                    )
                    | Q(
                        audience_type="selected_members",
                        group__isnull=True,
                        member_profile__isnull=False,
                    )
                ),
                name="valid_event_audience_target",
            ),
            models.UniqueConstraint(
                fields=["event"],
                condition=Q(audience_type="all_members"),
                name="unique_all_members_audience_per_event",
            ),
            models.UniqueConstraint(
                fields=["event", "group"],
                condition=Q(audience_type="group"),
                name="unique_group_audience_per_event",
            ),
            models.UniqueConstraint(
                fields=["event", "member_profile"],
                condition=Q(audience_type="selected_members"),
                name="unique_selected_member_audience_per_event",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.event} audience: {self.audience_type}"


class RSVP(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        YES = "yes", "Yes"
        NO = "no", "No"
        MAYBE = "maybe", "Maybe"
        NO_RESPONSE = "no_response", "No response"

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="rsvps",
    )
    member_profile = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="rsvps",
    )
    status = models.CharField(max_length=24, choices=Status.choices)
    note = models.TextField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["event__start_at", "member_profile__last_name", "member_profile__first_name"]
        indexes = [
            models.Index(fields=["event", "status"], name="rsvp_event_status_idx"),
            models.Index(fields=["member_profile", "event"], name="rsvp_member_event_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "member_profile"],
                name="unique_rsvp_per_event_member",
            )
        ]

    def __str__(self) -> str:
        return f"{self.member_profile} RSVP for {self.event}"


class AttendanceRecord(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        EXCUSED = "excused", "Excused"

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    member_profile = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    status = models.CharField(max_length=24, choices=Status.choices)
    note = models.TextField(null=True, blank=True)
    recorded_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_attendance_records",
    )
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["event__start_at", "member_profile__last_name", "member_profile__first_name"]
        indexes = [
            models.Index(fields=["event", "status"], name="attendance_event_status_idx"),
            models.Index(
                fields=["member_profile", "event"],
                name="attendance_member_event_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "member_profile"],
                name="unique_attendance_per_event_member",
            )
        ]

    def __str__(self) -> str:
        return f"{self.member_profile} attendance for {self.event}"
