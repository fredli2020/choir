from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.serializers import (
    OrganizationMembershipSerializer,
    OrganizationPermissionSerializer,
)
from apps.organizations.services import require_active_membership
from apps.permissions.services import get_membership_capabilities


class CurrentOrganizationMembershipView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, org_id):
        membership = require_active_membership(request.user, org_id)
        serializer = OrganizationMembershipSerializer(membership)
        return Response(serializer.data)


class OrganizationPermissionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, org_id):
        membership = require_active_membership(request.user, org_id)
        serializer = OrganizationPermissionSerializer(get_membership_capabilities(membership))
        return Response(serializer.data)
