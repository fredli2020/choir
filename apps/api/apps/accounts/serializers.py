from rest_framework import serializers

from apps.accounts.models import User
from apps.organizations.serializers import (
    MembershipSummarySerializer,
    OrganizationPermissionSerializer,
    OrganizationSerializer,
)


class CurrentUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "auth_provider_id", "email", "name", "created_at", "updated_at"]
        read_only_fields = fields


class CurrentUserOrganizationSerializer(serializers.Serializer):
    organization = OrganizationSerializer()
    membership = MembershipSummarySerializer()


class CurrentUserContextSerializer(serializers.Serializer):
    user = CurrentUserSerializer()
    organization = OrganizationSerializer(allow_null=True)
    membership = MembershipSummarySerializer(allow_null=True)
    permissions = OrganizationPermissionSerializer()
