from django.http import HttpResponseRedirect
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.integrations.google_calendar.serializers import (
    GoogleCalendarConnectionReadSerializer,
    GoogleCalendarConnectionStatusSerializer,
    GoogleCalendarListSerializer,
    GoogleCalendarOAuthStartSerializer,
    GoogleCalendarSelectionSerializer,
)
from apps.integrations.google_calendar.services import (
    build_google_oauth_authorization_url,
    disconnect_google_calendar,
    get_google_calendar_connection_status,
    handle_google_oauth_callback,
    list_google_calendars,
    select_google_calendar,
)
from apps.organizations.services import require_active_membership
from apps.permissions.services import require_can_manage_google_calendar


class OrganizationScopedAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_organization(self, request, org_id):
        membership = require_active_membership(request.user, org_id)
        return membership.organization


class GoogleCalendarConnectionStatusView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_google_calendar(request.user, organization)
        payload = get_google_calendar_connection_status(organization)
        return Response(GoogleCalendarConnectionStatusSerializer(payload).data)


class GoogleCalendarOAuthStartView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_google_calendar(request.user, organization)
        authorization_url = build_google_oauth_authorization_url(organization, request.user)
        return Response(
            GoogleCalendarOAuthStartSerializer({"authorization_url": authorization_url}).data
        )


class GoogleCalendarOAuthCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        redirect_url = handle_google_oauth_callback(
            code=request.query_params.get("code"),
            state=request.query_params.get("state"),
            error=request.query_params.get("error"),
        )
        return HttpResponseRedirect(redirect_url)


class GoogleCalendarCalendarsView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_google_calendar(request.user, organization)
        calendars = list_google_calendars(organization)
        return Response(GoogleCalendarListSerializer({"calendars": calendars}).data)


class GoogleCalendarSelectionView(OrganizationScopedAPIView):
    def put(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_google_calendar(request.user, organization)
        serializer = GoogleCalendarSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        connection = select_google_calendar(organization, serializer.validated_data["calendar_id"])
        return Response(GoogleCalendarConnectionReadSerializer(connection).data)


class GoogleCalendarDisconnectView(OrganizationScopedAPIView):
    def delete(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_google_calendar(request.user, organization)
        disconnect_google_calendar(organization)
        return Response(status=204)
