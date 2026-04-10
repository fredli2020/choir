from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import (
    CurrentUserContextSerializer,
    CurrentUserOrganizationSerializer,
    CurrentUserSerializer,
)
from apps.accounts.services import build_current_user_context
from apps.organizations.services import list_active_memberships


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = CurrentUserSerializer(request.user)
        return Response(serializer.data)


class CurrentUserOrganizationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = list_active_memberships(request.user)
        payload = [
            {"organization": membership.organization, "membership": membership}
            for membership in memberships
        ]
        serializer = CurrentUserOrganizationSerializer(payload, many=True)
        return Response(serializer.data)


class CurrentUserContextView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        context = build_current_user_context(
            request.user, request.query_params.get("organization_id")
        )
        serializer = CurrentUserContextSerializer(
            {
                "user": request.user,
                "organization": context.organization,
                "membership": context.membership,
                "permissions": context.permissions,
            }
        )
        return Response(serializer.data)
