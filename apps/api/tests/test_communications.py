import pytest

from apps.communications.models import CommunicationAudienceType, MessageCampaign, MessageRecipient
from apps.communications.providers import BaseEmailProvider, EmailProviderError, EmailSendResult
from apps.communications.services import (
    create_announcement,
    create_message_campaign,
    expand_communication_audience,
    publish_announcement,
    send_message_campaign,
)
from apps.members.models import GroupMember


class FlakyEmailProvider(BaseEmailProvider):
    def __init__(self, failing_email: str):
        self.failing_email = failing_email

    def send_email(self, *, to_email: str, subject: str, body: str) -> EmailSendResult:
        if to_email == self.failing_email:
            raise EmailProviderError("Mailbox rejected the message.")
        return EmailSendResult(provider_message_id=f"msg_{to_email}")


@pytest.mark.django_db
def test_expand_group_audience_returns_only_active_group_members(
    organization,
    section_group,
    section_leader_member_profile,
    member_profile,
    inactive_member_profile,
):
    GroupMember.objects.create(group=section_group, member_profile=member_profile, role="member")
    GroupMember.objects.create(group=section_group, member_profile=inactive_member_profile)

    audience = expand_communication_audience(
        organization,
        {
            "audience_type": CommunicationAudienceType.GROUP,
            "group_id": section_group.id,
        },
    )

    assert audience["group"] == section_group
    assert [member.id for member in audience["member_profiles"]] == [
        section_leader_member_profile.id,
        member_profile.id,
    ]
    assert audience["audience_description"] == "Group: Tenor Section (2 members)"


@pytest.mark.django_db
def test_member_feed_only_returns_published_targeted_announcements(
    api_client,
    organization,
    admin_user,
    member_user,
    member_membership,
    member_profile,
    section_group,
):
    all_members_announcement = create_announcement(
        organization,
        admin_user,
        {
            "title": "General Update",
            "body": "Full choir update.",
            "audience": {"audience_type": CommunicationAudienceType.ALL_MEMBERS},
        },
    )
    publish_announcement(all_members_announcement)

    selected_announcement = create_announcement(
        organization,
        admin_user,
        {
            "title": "Solo Reminder",
            "body": "Please review your line entrances.",
            "audience": {
                "audience_type": CommunicationAudienceType.SELECTED_MEMBERS,
                "member_profile_ids": [member_profile.id],
            },
        },
    )
    publish_announcement(selected_announcement)

    group_only_announcement = create_announcement(
        organization,
        admin_user,
        {
            "title": "Tenor Notes",
            "body": "Section-only notes.",
            "audience": {
                "audience_type": CommunicationAudienceType.GROUP,
                "group_id": section_group.id,
            },
        },
    )
    publish_announcement(group_only_announcement)

    create_announcement(
        organization,
        admin_user,
        {
            "title": "Draft Note",
            "body": "Not published yet.",
            "audience": {"audience_type": CommunicationAudienceType.ALL_MEMBERS},
        },
    )

    api_client.force_authenticate(user=member_user)
    response = api_client.get(f"/api/orgs/{member_membership.organization_id}/announcements/feed")

    assert response.status_code == 200
    titles = {item["title"] for item in response.json()}
    assert titles == {"General Update", "Solo Reminder"}


@pytest.mark.django_db
def test_send_message_campaign_marks_partial_failures(
    organization,
    admin_user,
    member_profile,
    unlinked_member_profile,
):
    campaign = create_message_campaign(
        organization,
        admin_user,
        {
            "subject": "Concert Week",
            "body": "Call time is 5:30 PM.",
            "audience": {
                "audience_type": CommunicationAudienceType.SELECTED_MEMBERS,
                "member_profile_ids": [member_profile.id, unlinked_member_profile.id],
            },
        },
    )

    updated_campaign = send_message_campaign(
        campaign,
        provider=FlakyEmailProvider(failing_email=member_profile.email),
    )

    assert updated_campaign.status == MessageCampaign.Status.FAILED
    recipients = {recipient.email: recipient for recipient in updated_campaign.recipients.all()}
    assert (
        recipients[member_profile.email].delivery_status
        == MessageRecipient.DeliveryStatus.FAILED
    )
    assert recipients[member_profile.email].error == "Mailbox rejected the message."
    assert (
        recipients[unlinked_member_profile.email].delivery_status
        == MessageRecipient.DeliveryStatus.SENT
    )
