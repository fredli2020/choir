from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import UUIDModel, UUIDTimeStampedModel
from apps.members.models import Group, MemberProfile
from apps.organizations.models import Organization


class CommunicationAudienceType(models.TextChoices):
    ALL_MEMBERS = "all_members", "All members"
    GROUP = "group", "Group"
    SELECTED_MEMBERS = "selected_members", "Selected members"


class Announcement(UUIDTimeStampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="announcements",
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_announcements",
    )

    class Meta:
        ordering = ["-published_at", "-created_at", "title"]

    def __str__(self) -> str:
        return self.title


class AnnouncementAudience(UUIDModel):
    announcement = models.ForeignKey(
        Announcement,
        on_delete=models.CASCADE,
        related_name="audiences",
    )
    audience_type = models.CharField(max_length=32, choices=CommunicationAudienceType.choices)
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="announcement_audiences",
    )
    member_profile = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="announcement_audiences",
    )

    class Meta:
        ordering = ["audience_type", "group__name", "member_profile__last_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["announcement", "audience_type"],
                condition=Q(group__isnull=True, member_profile__isnull=True),
                name="unique_announcement_all_members_audience",
            ),
            models.UniqueConstraint(
                fields=["announcement", "audience_type", "group"],
                condition=Q(group__isnull=False),
                name="unique_announcement_group_audience",
            ),
            models.UniqueConstraint(
                fields=["announcement", "audience_type", "member_profile"],
                condition=Q(member_profile__isnull=False),
                name="unique_announcement_member_audience",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.announcement} audience"


class MessageCampaign(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENDING = "sending", "Sending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="message_campaigns",
    )
    subject = models.CharField(max_length=255)
    body = models.TextField()
    audience_description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_message_campaigns",
    )

    class Meta:
        ordering = ["-created_at", "subject"]

    def __str__(self) -> str:
        return self.subject


class MessageRecipient(UUIDTimeStampedModel):
    class DeliveryStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    message_campaign = models.ForeignKey(
        MessageCampaign,
        on_delete=models.CASCADE,
        related_name="recipients",
    )
    member_profile = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="message_recipients",
    )
    email = models.EmailField()
    delivery_status = models.CharField(
        max_length=16,
        choices=DeliveryStatus.choices,
        default=DeliveryStatus.PENDING,
    )
    error = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["member_profile__last_name", "member_profile__first_name", "email"]
        constraints = [
            models.UniqueConstraint(
                fields=["message_campaign", "member_profile"],
                name="unique_campaign_member_recipient",
            )
        ]

    def __str__(self) -> str:
        return f"{self.email} for {self.message_campaign}"
