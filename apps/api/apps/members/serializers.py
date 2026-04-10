from rest_framework import serializers

from apps.accounts.models import User
from apps.members.models import Group, GroupMember, MemberProfile


class MemberProfileReadSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(read_only=True)
    user_id = serializers.UUIDField(allow_null=True, read_only=True)

    class Meta:
        model = MemberProfile
        fields = [
            "id",
            "organization_id",
            "user_id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "voice_part",
            "status",
            "notes",
            "joined_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class MemberProfileWriteSerializer(serializers.Serializer):
    user_id = serializers.UUIDField(required=False, allow_null=True)
    first_name = serializers.CharField(max_length=120)
    last_name = serializers.CharField(max_length=120)
    email = serializers.EmailField()
    phone = serializers.CharField(
        max_length=40,
        allow_blank=True,
        allow_null=True,
        required=False,
    )
    voice_part = serializers.ChoiceField(
        choices=MemberProfile.VoicePart.choices,
        allow_null=True,
        required=False,
    )
    status = serializers.ChoiceField(
        choices=MemberProfile.Status.choices,
        required=False,
    )
    notes = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    joined_at = serializers.DateField(allow_null=True, required=False)

    def validate_user_id(self, value):
        if value is None:
            return None

        try:
            return User.objects.get(id=value)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError("User not found.") from exc


class MemberProfileSelfUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=120, required=False)
    last_name = serializers.CharField(max_length=120, required=False)
    phone = serializers.CharField(
        max_length=40,
        allow_blank=True,
        allow_null=True,
        required=False,
    )


class DirectoryMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberProfile
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "voice_part",
            "status",
        ]
        read_only_fields = fields


class GroupMemberSummarySerializer(serializers.ModelSerializer):
    member_profile_id = serializers.UUIDField(read_only=True)
    first_name = serializers.CharField(source="member_profile.first_name", read_only=True)
    last_name = serializers.CharField(source="member_profile.last_name", read_only=True)
    email = serializers.EmailField(source="member_profile.email", read_only=True)
    voice_part = serializers.CharField(source="member_profile.voice_part", read_only=True)

    class Meta:
        model = GroupMember
        fields = [
            "id",
            "member_profile_id",
            "first_name",
            "last_name",
            "email",
            "voice_part",
            "role",
            "created_at",
        ]
        read_only_fields = fields


class GroupReadSerializer(serializers.ModelSerializer):
    organization_id = serializers.UUIDField(read_only=True)
    members = GroupMemberSummarySerializer(
        source="group_memberships",
        many=True,
        read_only=True,
    )

    class Meta:
        model = Group
        fields = [
            "id",
            "organization_id",
            "type",
            "name",
            "description",
            "members",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class GroupWriteSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=Group.Type.choices)
    name = serializers.CharField(max_length=120)
    description = serializers.CharField(allow_blank=True, allow_null=True, required=False)


class GroupAssignmentSerializer(serializers.Serializer):
    member_profile_id = serializers.UUIDField()
    role = serializers.CharField(max_length=120, allow_blank=True, allow_null=True, required=False)
