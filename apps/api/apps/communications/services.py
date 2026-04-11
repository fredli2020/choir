from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.communications.filters import MessageCampaignFilterSet
from apps.communications.models import (
    Announcement,
    AnnouncementAudience,
    CommunicationAudienceType,
    MessageCampaign,
    MessageRecipient,
)
from apps.communications.providers import BaseEmailProvider, EmailProviderError, get_email_provider
from apps.members.models import Group, MemberProfile
from apps.organizations.models import Organization


def _normalize_text(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValidationError("This field may not be blank.")
    return normalized


def _normalize_optional_text(value):
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _active_member_profiles_queryset(organization: Organization):
    return MemberProfile.objects.filter(
        organization=organization,
        status=MemberProfile.Status.ACTIVE,
    )


def _base_announcement_queryset():
    return Announcement.objects.select_related("organization", "created_by_user").prefetch_related(
        "audiences__group",
        "audiences__member_profile",
    )


def _base_campaign_queryset():
    return MessageCampaign.objects.select_related(
        "organization",
        "created_by_user",
    ).prefetch_related(
        "recipients__member_profile",
    )


def _resolve_group(organization: Organization, group_id):
    return Group.objects.get(id=group_id, organization=organization)


def _resolve_member_profiles(organization: Organization, member_profile_ids: list):
    unique_ids = list(dict.fromkeys(str(member_id) for member_id in member_profile_ids))
    if len(unique_ids) != len(member_profile_ids):
        raise ValidationError(
            {"member_profile_ids": ["Duplicate member profiles are not allowed."]}
        )

    member_profiles = list(
        _active_member_profiles_queryset(organization)
        .filter(id__in=unique_ids)
        .order_by("last_name", "first_name", "email")
    )
    if len(member_profiles) != len(unique_ids):
        raise ValidationError(
            {
                "member_profile_ids": [
                    "Every selected member must be active and in the organization."
                ]
            }
        )
    return member_profiles


def expand_communication_audience(organization: Organization, audience_data: dict) -> dict:
    audience_type = audience_data["audience_type"]
    group_id = audience_data.get("group_id")
    member_profile_ids = audience_data.get("member_profile_ids") or []

    if audience_type == CommunicationAudienceType.ALL_MEMBERS:
        if group_id or member_profile_ids:
            raise ValidationError(
                {"audience": ["All-members audience cannot include a group or selected members."]}
            )
        members = list(
            _active_member_profiles_queryset(organization).order_by(
                "last_name",
                "first_name",
                "email",
            )
        )
        return {
            "audience_type": audience_type,
            "group": None,
            "member_profiles": members,
            "audience_description": f"All active members ({len(members)})",
        }

    if audience_type == CommunicationAudienceType.GROUP:
        if not group_id:
            raise ValidationError({"group_id": ["A group audience requires a group_id."]})
        if member_profile_ids:
            raise ValidationError(
                {"member_profile_ids": ["Group audience cannot include selected members."]}
            )
        try:
            group = _resolve_group(organization, group_id)
        except Group.DoesNotExist as exc:
            raise ValidationError({"group_id": ["Group not found in this organization."]}) from exc
        members = list(
            _active_member_profiles_queryset(organization)
            .filter(group_memberships__group=group)
            .distinct()
            .order_by("last_name", "first_name", "email")
        )
        return {
            "audience_type": audience_type,
            "group": group,
            "member_profiles": members,
            "audience_description": f"Group: {group.name} ({len(members)} members)",
        }

    if audience_type == CommunicationAudienceType.SELECTED_MEMBERS:
        if group_id:
            raise ValidationError(
                {"group_id": ["Selected-members audience cannot include a group."]}
            )
        if not member_profile_ids:
            raise ValidationError(
                {"member_profile_ids": ["Selected-members audience requires at least one member."]}
            )
        members = _resolve_member_profiles(organization, member_profile_ids)
        return {
            "audience_type": audience_type,
            "group": None,
            "member_profiles": members,
            "audience_description": f"Selected members ({len(members)})",
        }

    raise ValidationError({"audience_type": ["Unsupported audience type."]})


def _announcement_member_profile_for_user(organization: Organization, user) -> MemberProfile | None:
    if not getattr(user, "is_authenticated", False):
        return None
    return (
        MemberProfile.objects.filter(
            organization=organization,
            user=user,
            status=MemberProfile.Status.ACTIVE,
        )
        .select_related("organization", "user")
        .first()
    )


def _get_announcement_targeted_members_queryset(announcement: Announcement):
    audience_rows = list(announcement.audiences.all())
    if not audience_rows:
        return MemberProfile.objects.none()

    audience_type = audience_rows[0].audience_type
    if audience_type == CommunicationAudienceType.ALL_MEMBERS:
        return _active_member_profiles_queryset(announcement.organization).order_by(
            "last_name", "first_name", "email"
        )

    if audience_type == CommunicationAudienceType.GROUP:
        group = audience_rows[0].group
        return (
            _active_member_profiles_queryset(announcement.organization)
            .filter(group_memberships__group=group)
            .distinct()
            .order_by("last_name", "first_name", "email")
        )

    member_ids = [row.member_profile_id for row in audience_rows if row.member_profile_id]
    return _active_member_profiles_queryset(announcement.organization).filter(
        id__in=member_ids
    ).order_by("last_name", "first_name", "email")


def get_announcement_targeted_members(announcement: Announcement) -> list[MemberProfile]:
    return list(_get_announcement_targeted_members_queryset(announcement))


def get_announcement_audience_summary(announcement: Announcement) -> dict:
    audience_rows = list(announcement.audiences.all())
    if not audience_rows:
        return {
            "audience_type": None,
            "group": None,
            "selected_members": [],
            "member_count": 0,
        }

    audience_type = audience_rows[0].audience_type
    if audience_type == CommunicationAudienceType.GROUP:
        group = audience_rows[0].group
        members = get_announcement_targeted_members(announcement)
        return {
            "audience_type": audience_type,
            "group": group,
            "selected_members": [],
            "member_count": len(members),
        }

    if audience_type == CommunicationAudienceType.SELECTED_MEMBERS:
        members = get_announcement_targeted_members(announcement)
        return {
            "audience_type": audience_type,
            "group": None,
            "selected_members": members,
            "member_count": len(members),
        }

    members = get_announcement_targeted_members(announcement)
    return {
        "audience_type": audience_type,
        "group": None,
        "selected_members": [],
        "member_count": len(members),
    }


def list_announcements(organization: Organization):
    return _base_announcement_queryset().filter(organization=organization)


def list_published_announcements_for_user(organization: Organization, user):
    member_profile = _announcement_member_profile_for_user(organization, user)
    queryset = _base_announcement_queryset().filter(
        organization=organization,
        published=True,
    )

    filters = Q(audiences__audience_type=CommunicationAudienceType.ALL_MEMBERS)
    if member_profile is not None:
        filters |= Q(
            audiences__audience_type=CommunicationAudienceType.GROUP,
            audiences__group__group_memberships__member_profile=member_profile,
        )
        filters |= Q(
            audiences__audience_type=CommunicationAudienceType.SELECTED_MEMBERS,
            audiences__member_profile=member_profile,
        )

    return queryset.filter(filters).distinct()


def get_announcement(organization: Organization, announcement_id) -> Announcement:
    return _base_announcement_queryset().get(id=announcement_id, organization=organization)


def get_published_announcement_for_user(
    organization: Organization,
    announcement_id,
    user,
) -> Announcement:
    return list_published_announcements_for_user(organization, user).get(id=announcement_id)


def _ensure_announcement_is_editable(announcement: Announcement) -> None:
    if announcement.published:
        raise ValidationError(
            {"announcement": ["Published announcements cannot be edited."]}
        )


@transaction.atomic
def replace_announcement_audience(announcement: Announcement, audience_data: dict) -> Announcement:
    _ensure_announcement_is_editable(announcement)
    resolved_audience = expand_communication_audience(announcement.organization, audience_data)
    AnnouncementAudience.objects.filter(announcement=announcement).delete()

    if resolved_audience["audience_type"] == CommunicationAudienceType.ALL_MEMBERS:
        AnnouncementAudience.objects.create(
            announcement=announcement,
            audience_type=CommunicationAudienceType.ALL_MEMBERS,
        )
    elif resolved_audience["audience_type"] == CommunicationAudienceType.GROUP:
        AnnouncementAudience.objects.create(
            announcement=announcement,
            audience_type=CommunicationAudienceType.GROUP,
            group=resolved_audience["group"],
        )
    else:
        AnnouncementAudience.objects.bulk_create(
            [
                AnnouncementAudience(
                    announcement=announcement,
                    audience_type=CommunicationAudienceType.SELECTED_MEMBERS,
                    member_profile=member_profile,
                )
                for member_profile in resolved_audience["member_profiles"]
            ]
        )

    return get_announcement(announcement.organization, announcement.id)


@transaction.atomic
def create_announcement(organization: Organization, user, data: dict) -> Announcement:
    announcement = Announcement.objects.create(
        organization=organization,
        title=_normalize_text(data["title"]),
        body=_normalize_text(data["body"]),
        created_by_user=user,
    )
    audience_data = data.get("audience")
    if audience_data:
        announcement = replace_announcement_audience(announcement, audience_data)
    return get_announcement(organization, announcement.id)


def update_announcement(announcement: Announcement, data: dict) -> Announcement:
    _ensure_announcement_is_editable(announcement)
    if "title" in data:
        announcement.title = _normalize_text(data["title"])
    if "body" in data:
        announcement.body = _normalize_text(data["body"])
    announcement.save(update_fields=["title", "body", "updated_at"])
    return get_announcement(announcement.organization, announcement.id)


def publish_announcement(announcement: Announcement) -> Announcement:
    _ensure_announcement_is_editable(announcement)
    if not announcement.audiences.exists():
        raise ValidationError(
            {"audience": ["Announcement audience must be set before publishing."]}
        )

    announcement.published = True
    announcement.published_at = timezone.now()
    announcement.save(update_fields=["published", "published_at", "updated_at"])
    return get_announcement(announcement.organization, announcement.id)


def list_message_campaigns(organization: Organization, filters: dict | None = None):
    queryset = _base_campaign_queryset().filter(organization=organization).order_by("-created_at")
    if filters is None:
        return queryset
    filterset = MessageCampaignFilterSet(filters, queryset=queryset)
    if not filterset.is_valid():
        raise ValidationError(filterset.errors)
    return filterset.qs


def get_message_campaign(organization: Organization, campaign_id) -> MessageCampaign:
    return _base_campaign_queryset().get(id=campaign_id, organization=organization)


def _ensure_campaign_is_editable(campaign: MessageCampaign) -> None:
    if campaign.status != MessageCampaign.Status.DRAFT:
        raise ValidationError(
            {"campaign": ["Only draft campaigns can be edited or sent."]}
        )


@transaction.atomic
def create_message_campaign(organization: Organization, user, data: dict) -> MessageCampaign:
    campaign = MessageCampaign.objects.create(
        organization=organization,
        subject=_normalize_text(data["subject"]),
        body=_normalize_text(data["body"]),
        created_by_user=user,
    )
    audience_data = data.get("audience")
    if audience_data:
        campaign = prepare_message_campaign_recipients(campaign, audience_data)
    return get_message_campaign(organization, campaign.id)


def update_message_campaign(campaign: MessageCampaign, data: dict) -> MessageCampaign:
    _ensure_campaign_is_editable(campaign)
    if "subject" in data:
        campaign.subject = _normalize_text(data["subject"])
    if "body" in data:
        campaign.body = _normalize_text(data["body"])
    campaign.save(update_fields=["subject", "body", "updated_at"])
    return get_message_campaign(campaign.organization, campaign.id)


@transaction.atomic
def prepare_message_campaign_recipients(
    campaign: MessageCampaign,
    audience_data: dict,
) -> MessageCampaign:
    _ensure_campaign_is_editable(campaign)
    resolved_audience = expand_communication_audience(campaign.organization, audience_data)

    MessageRecipient.objects.filter(message_campaign=campaign).delete()
    MessageRecipient.objects.bulk_create(
        [
            MessageRecipient(
                message_campaign=campaign,
                member_profile=member_profile,
                email=member_profile.email,
            )
            for member_profile in resolved_audience["member_profiles"]
        ]
    )

    campaign.audience_description = resolved_audience["audience_description"]
    campaign.save(update_fields=["audience_description", "updated_at"])
    return get_message_campaign(campaign.organization, campaign.id)


def get_message_campaign_results_summary(campaign: MessageCampaign) -> dict:
    counts = {
        MessageRecipient.DeliveryStatus.PENDING: 0,
        MessageRecipient.DeliveryStatus.SENT: 0,
        MessageRecipient.DeliveryStatus.FAILED: 0,
    }
    for recipient in campaign.recipients.all():
        counts[recipient.delivery_status] = counts.get(recipient.delivery_status, 0) + 1

    return {
        "pending": counts[MessageRecipient.DeliveryStatus.PENDING],
        "sent": counts[MessageRecipient.DeliveryStatus.SENT],
        "failed": counts[MessageRecipient.DeliveryStatus.FAILED],
        "total": counts[MessageRecipient.DeliveryStatus.PENDING]
        + counts[MessageRecipient.DeliveryStatus.SENT]
        + counts[MessageRecipient.DeliveryStatus.FAILED],
    }


def send_message_campaign(
    campaign: MessageCampaign,
    *,
    provider: BaseEmailProvider | None = None,
) -> MessageCampaign:
    _ensure_campaign_is_editable(campaign)
    recipients = list(campaign.recipients.select_related("member_profile").all())
    if not recipients:
        raise ValidationError(
            {"audience": ["Campaign must have at least one recipient before sending."]}
        )

    try:
        provider = provider or get_email_provider()
    except EmailProviderError as exc:
        raise ValidationError({"provider": [str(exc)]}) from exc

    campaign.status = MessageCampaign.Status.SENDING
    campaign.save(update_fields=["status", "updated_at"])

    had_failures = False
    try:
        for recipient in recipients:
            try:
                provider.send_email(
                    to_email=recipient.email,
                    subject=campaign.subject,
                    body=campaign.body,
                )
                recipient.delivery_status = MessageRecipient.DeliveryStatus.SENT
                recipient.error = None
            except Exception as exc:
                had_failures = True
                recipient.delivery_status = MessageRecipient.DeliveryStatus.FAILED
                recipient.error = _normalize_optional_text(str(exc)) or "Unknown delivery error."
            recipient.save(update_fields=["delivery_status", "error", "updated_at"])
    except Exception:
        campaign.status = MessageCampaign.Status.FAILED
        campaign.sent_at = None
        campaign.save(update_fields=["status", "sent_at", "updated_at"])
        raise

    if had_failures:
        campaign.status = MessageCampaign.Status.FAILED
        campaign.sent_at = None
    else:
        campaign.status = MessageCampaign.Status.SENT
        campaign.sent_at = timezone.now()
    campaign.save(update_fields=["status", "sent_at", "updated_at"])
    return get_message_campaign(campaign.organization, campaign.id)
