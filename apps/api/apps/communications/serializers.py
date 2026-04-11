from rest_framework import serializers

from apps.communications.models import (
    Announcement,
    CommunicationAudienceType,
    MessageCampaign,
    MessageRecipient,
)
from apps.communications.services import (
    get_announcement_audience_summary,
    get_message_campaign_results_summary,
)
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


class CommunicationAudienceWriteSerializer(serializers.Serializer):
    audience_type = serializers.ChoiceField(choices=CommunicationAudienceType.choices)
    group_id = serializers.UUIDField(required=False, allow_null=True)
    member_profile_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )


class AnnouncementWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    audience = CommunicationAudienceWriteSerializer(required=False)


class AnnouncementAudienceSummarySerializer(serializers.Serializer):
    audience_type = serializers.CharField(allow_null=True)
    group = GroupAudienceSerializer(allow_null=True)
    selected_members = MemberProfileSummarySerializer(many=True)
    member_count = serializers.IntegerField()


class AnnouncementReadSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(read_only=True)
    created_by_user_id = serializers.UUIDField(allow_null=True, read_only=True)
    audience = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = [
            "id",
            "organization_id",
            "title",
            "body",
            "published",
            "published_at",
            "created_by_user_id",
            "audience",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_audience(self, obj):
        return AnnouncementAudienceSummarySerializer(get_announcement_audience_summary(obj)).data


class MessageCampaignWriteSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=255)
    body = serializers.CharField()
    audience = CommunicationAudienceWriteSerializer(required=False)


class MessageCampaignSummarySerializer(serializers.Serializer):
    pending = serializers.IntegerField()
    sent = serializers.IntegerField()
    failed = serializers.IntegerField()
    total = serializers.IntegerField()


class MessageRecipientReadSerializer(serializers.ModelSerializer):
    member_profile = MemberProfileSummarySerializer(read_only=True)

    class Meta:
        model = MessageRecipient
        fields = [
            "id",
            "member_profile",
            "email",
            "delivery_status",
            "error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MessageCampaignReadSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(read_only=True)
    created_by_user_id = serializers.UUIDField(allow_null=True, read_only=True)
    recipient_count = serializers.SerializerMethodField()
    results_summary = serializers.SerializerMethodField()

    class Meta:
        model = MessageCampaign
        fields = [
            "id",
            "organization_id",
            "subject",
            "body",
            "audience_description",
            "status",
            "sent_at",
            "created_by_user_id",
            "recipient_count",
            "results_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_recipient_count(self, obj):
        return obj.recipients.count()

    def get_results_summary(self, obj):
        return MessageCampaignSummarySerializer(get_message_campaign_results_summary(obj)).data


class MessageCampaignAudienceSerializer(serializers.Serializer):
    audience_description = serializers.CharField(allow_null=True)
    recipients = MessageRecipientReadSerializer(many=True)
    recipient_count = serializers.IntegerField()


class MessageCampaignResultsSerializer(serializers.Serializer):
    campaign = MessageCampaignReadSerializer()
    summary = MessageCampaignSummarySerializer()
    recipients = MessageRecipientReadSerializer(many=True)
