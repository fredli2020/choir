from rest_framework import serializers

from apps.organizations.models import Organization, OrganizationMembership


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "created_at", "updated_at"]
        read_only_fields = fields


class MembershipSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationMembership
        fields = ["id", "role", "status", "created_at", "updated_at"]
        read_only_fields = fields


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = OrganizationMembership
        fields = [
            "id",
            "organization",
            "role",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class OrganizationPermissionSerializer(serializers.Serializer):
    can_manage_members = serializers.BooleanField()
    can_manage_groups = serializers.BooleanField()
    can_view_members = serializers.BooleanField()
    can_manage_events = serializers.BooleanField()
    can_record_attendance = serializers.BooleanField()
    can_send_messages = serializers.BooleanField()
    can_manage_google_calendar = serializers.BooleanField()
    can_view_directory = serializers.BooleanField()
    can_self_edit_profile = serializers.BooleanField()
