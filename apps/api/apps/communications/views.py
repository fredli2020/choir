from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.communications.models import Announcement, MessageCampaign
from apps.communications.serializers import (
    AnnouncementReadSerializer,
    AnnouncementWriteSerializer,
    CommunicationAudienceWriteSerializer,
    MessageCampaignAudienceSerializer,
    MessageCampaignReadSerializer,
    MessageCampaignResultsSerializer,
    MessageCampaignWriteSerializer,
)
from apps.communications.services import (
    create_announcement,
    create_message_campaign,
    get_announcement,
    get_message_campaign,
    get_message_campaign_results_summary,
    get_published_announcement_for_user,
    list_announcements,
    list_message_campaigns,
    list_published_announcements_for_user,
    prepare_message_campaign_recipients,
    publish_announcement,
    replace_announcement_audience,
    send_message_campaign,
    update_announcement,
    update_message_campaign,
)
from apps.organizations.services import require_active_membership
from apps.permissions.services import require_can_send_messages


class OrganizationScopedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_organization(self, request, org_id):
        membership = require_active_membership(request.user, org_id)
        return membership.organization

    def handle_domain_error(self, exc):
        if isinstance(exc, DjangoPermissionDenied):
            raise PermissionDenied(str(exc)) from exc
        if isinstance(exc, DjangoValidationError):
            detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
            raise ValidationError(detail) from exc
        raise exc


class AnnouncementListCreateView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        announcements = list_announcements(organization)
        return Response(AnnouncementReadSerializer(announcements, many=True).data)

    def post(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        serializer = AnnouncementWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            announcement = create_announcement(
                organization,
                request.user,
                serializer.validated_data,
            )
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(AnnouncementReadSerializer(announcement).data, status=201)


class AnnouncementDetailView(OrganizationScopedAPIView):
    def get(self, request, org_id, announcement_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        try:
            announcement = get_announcement(organization, announcement_id)
        except Announcement.DoesNotExist as exc:
            raise NotFound("Announcement not found.") from exc
        return Response(AnnouncementReadSerializer(announcement).data)

    def patch(self, request, org_id, announcement_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        serializer = AnnouncementWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            announcement = get_announcement(organization, announcement_id)
            announcement = update_announcement(announcement, serializer.validated_data)
        except Announcement.DoesNotExist as exc:
            raise NotFound("Announcement not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(AnnouncementReadSerializer(announcement).data)


class AnnouncementAudienceView(OrganizationScopedAPIView):
    def get(self, request, org_id, announcement_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        try:
            announcement = get_announcement(organization, announcement_id)
        except Announcement.DoesNotExist as exc:
            raise NotFound("Announcement not found.") from exc
        return Response(AnnouncementReadSerializer(announcement).data["audience"])

    def put(self, request, org_id, announcement_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        serializer = CommunicationAudienceWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            announcement = get_announcement(organization, announcement_id)
            announcement = replace_announcement_audience(announcement, serializer.validated_data)
        except Announcement.DoesNotExist as exc:
            raise NotFound("Announcement not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(AnnouncementReadSerializer(announcement).data["audience"])


class AnnouncementPublishView(OrganizationScopedAPIView):
    def post(self, request, org_id, announcement_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        try:
            announcement = get_announcement(organization, announcement_id)
            announcement = publish_announcement(announcement)
        except Announcement.DoesNotExist as exc:
            raise NotFound("Announcement not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(AnnouncementReadSerializer(announcement).data)


class AnnouncementFeedView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        announcements = list_published_announcements_for_user(organization, request.user)
        return Response(AnnouncementReadSerializer(announcements, many=True).data)


class AnnouncementFeedDetailView(OrganizationScopedAPIView):
    def get(self, request, org_id, announcement_id):
        organization = self.get_organization(request, org_id)
        try:
            announcement = get_published_announcement_for_user(
                organization,
                announcement_id,
                request.user,
            )
        except Announcement.DoesNotExist as exc:
            raise NotFound("Announcement not found.") from exc
        return Response(AnnouncementReadSerializer(announcement).data)


class MessageCampaignListCreateView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        try:
            campaigns = list_message_campaigns(organization, request.query_params)
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(MessageCampaignReadSerializer(campaigns, many=True).data)

    def post(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        serializer = MessageCampaignWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            campaign = create_message_campaign(
                organization,
                request.user,
                serializer.validated_data,
            )
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(MessageCampaignReadSerializer(campaign).data, status=201)


class MessageCampaignDetailView(OrganizationScopedAPIView):
    def get(self, request, org_id, campaign_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        try:
            campaign = get_message_campaign(organization, campaign_id)
        except MessageCampaign.DoesNotExist as exc:
            raise NotFound("Message campaign not found.") from exc
        return Response(MessageCampaignReadSerializer(campaign).data)

    def patch(self, request, org_id, campaign_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        serializer = MessageCampaignWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            campaign = get_message_campaign(organization, campaign_id)
            campaign = update_message_campaign(campaign, serializer.validated_data)
        except MessageCampaign.DoesNotExist as exc:
            raise NotFound("Message campaign not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(MessageCampaignReadSerializer(campaign).data)


class MessageCampaignAudienceView(OrganizationScopedAPIView):
    def get(self, request, org_id, campaign_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        try:
            campaign = get_message_campaign(organization, campaign_id)
        except MessageCampaign.DoesNotExist as exc:
            raise NotFound("Message campaign not found.") from exc
        payload = {
            "audience_description": campaign.audience_description,
            "recipients": campaign.recipients.all(),
            "recipient_count": campaign.recipients.count(),
        }
        return Response(MessageCampaignAudienceSerializer(payload).data)

    def put(self, request, org_id, campaign_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        serializer = CommunicationAudienceWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            campaign = get_message_campaign(organization, campaign_id)
            campaign = prepare_message_campaign_recipients(campaign, serializer.validated_data)
        except MessageCampaign.DoesNotExist as exc:
            raise NotFound("Message campaign not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        payload = {
            "audience_description": campaign.audience_description,
            "recipients": campaign.recipients.all(),
            "recipient_count": campaign.recipients.count(),
        }
        return Response(MessageCampaignAudienceSerializer(payload).data)


class MessageCampaignSendView(OrganizationScopedAPIView):
    def post(self, request, org_id, campaign_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        try:
            campaign = get_message_campaign(organization, campaign_id)
            campaign = send_message_campaign(campaign)
        except MessageCampaign.DoesNotExist as exc:
            raise NotFound("Message campaign not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(MessageCampaignReadSerializer(campaign).data)


class MessageCampaignResultsView(OrganizationScopedAPIView):
    def get(self, request, org_id, campaign_id):
        organization = self.get_organization(request, org_id)
        require_can_send_messages(request.user, organization)
        try:
            campaign = get_message_campaign(organization, campaign_id)
        except MessageCampaign.DoesNotExist as exc:
            raise NotFound("Message campaign not found.") from exc
        payload = {
            "campaign": campaign,
            "summary": get_message_campaign_results_summary(campaign),
            "recipients": campaign.recipients.all(),
        }
        return Response(MessageCampaignResultsSerializer(payload).data)
