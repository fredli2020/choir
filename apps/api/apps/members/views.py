from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.members.models import Group, GroupMember, MemberProfile
from apps.members.serializers import (
    DirectoryMemberSerializer,
    GroupAssignmentSerializer,
    GroupMemberSummarySerializer,
    GroupReadSerializer,
    GroupWriteSerializer,
    MemberProfileReadSerializer,
    MemberProfileSelfUpdateSerializer,
    MemberProfileWriteSerializer,
)
from apps.members.services import (
    assign_member_to_group,
    create_group,
    create_member_profile,
    delete_group,
    delete_member_profile,
    get_group,
    get_member_profile,
    get_my_member_profile,
    list_directory_members,
    list_groups,
    list_member_profiles,
    remove_member_from_group,
    update_group,
    update_member_profile,
    update_my_member_profile,
)
from apps.organizations.services import require_active_membership
from apps.permissions.services import (
    require_can_manage_groups,
    require_can_manage_members,
    require_can_self_edit_profile,
    require_can_view_directory,
    require_can_view_members,
)


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


class MemberListCreateView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_view_members(request.user, organization)
        try:
            members = list_member_profiles(organization, request.query_params)
        except Exception as exc:
            self.handle_domain_error(exc)
        serializer = MemberProfileReadSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_members(request.user, organization)
        serializer = MemberProfileWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            member_profile = create_member_profile(organization, serializer.validated_data)
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(MemberProfileReadSerializer(member_profile).data, status=201)


class MemberDetailView(OrganizationScopedAPIView):
    def get(self, request, org_id, member_id):
        organization = self.get_organization(request, org_id)
        require_can_view_members(request.user, organization)
        try:
            member_profile = get_member_profile(organization, member_id)
        except MemberProfile.DoesNotExist as exc:
            raise NotFound("Member profile not found.") from exc
        serializer = MemberProfileReadSerializer(member_profile)
        return Response(serializer.data)

    def patch(self, request, org_id, member_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_members(request.user, organization)
        serializer = MemberProfileWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            member_profile = get_member_profile(organization, member_id)
            member_profile = update_member_profile(member_profile, serializer.validated_data)
        except MemberProfile.DoesNotExist as exc:
            raise NotFound("Member profile not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(MemberProfileReadSerializer(member_profile).data)

    def delete(self, request, org_id, member_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_members(request.user, organization)
        try:
            member_profile = get_member_profile(organization, member_id)
            delete_member_profile(member_profile)
        except MemberProfile.DoesNotExist as exc:
            raise NotFound("Member profile not found.") from exc
        return Response(status=204)


class DirectoryView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_view_directory(request.user, organization)
        try:
            members = list_directory_members(organization, request.query_params)
        except Exception as exc:
            self.handle_domain_error(exc)
        serializer = DirectoryMemberSerializer(members, many=True)
        return Response(serializer.data)


class MyProfileView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_self_edit_profile(request.user, organization)
        try:
            member_profile = get_my_member_profile(organization, request.user)
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(MemberProfileReadSerializer(member_profile).data)

    def patch(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_self_edit_profile(request.user, organization)
        serializer = MemberProfileSelfUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            member_profile = get_my_member_profile(organization, request.user)
            member_profile = update_my_member_profile(member_profile, serializer.validated_data)
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(MemberProfileReadSerializer(member_profile).data)


class GroupListCreateView(OrganizationScopedAPIView):
    def get(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_view_members(request.user, organization)
        try:
            groups = list_groups(organization, request.query_params)
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(GroupReadSerializer(groups, many=True).data)

    def post(self, request, org_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_groups(request.user, organization)
        serializer = GroupWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            group = create_group(organization, serializer.validated_data)
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(GroupReadSerializer(group).data, status=201)


class GroupDetailView(OrganizationScopedAPIView):
    def get(self, request, org_id, group_id):
        organization = self.get_organization(request, org_id)
        require_can_view_members(request.user, organization)
        try:
            group = get_group(organization, group_id)
        except Group.DoesNotExist as exc:
            raise NotFound("Group not found.") from exc
        return Response(GroupReadSerializer(group).data)

    def patch(self, request, org_id, group_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_groups(request.user, organization)
        serializer = GroupWriteSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            group = get_group(organization, group_id)
            group = update_group(group, serializer.validated_data)
        except Group.DoesNotExist as exc:
            raise NotFound("Group not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(GroupReadSerializer(group).data)

    def delete(self, request, org_id, group_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_groups(request.user, organization)
        try:
            group = get_group(organization, group_id)
            delete_group(group)
        except Group.DoesNotExist as exc:
            raise NotFound("Group not found.") from exc
        return Response(status=204)


class GroupAssignmentCreateView(OrganizationScopedAPIView):
    def post(self, request, org_id, group_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_groups(request.user, organization)
        serializer = GroupAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            group = get_group(organization, group_id)
            member_profile = get_member_profile(
                organization,
                serializer.validated_data["member_profile_id"],
            )
            assignment = assign_member_to_group(
                group,
                member_profile,
                serializer.validated_data.get("role"),
            )
        except Group.DoesNotExist as exc:
            raise NotFound("Group not found.") from exc
        except MemberProfile.DoesNotExist as exc:
            raise NotFound("Member profile not found.") from exc
        except Exception as exc:
            self.handle_domain_error(exc)
        return Response(GroupMemberSummarySerializer(assignment).data, status=201)


class GroupAssignmentDeleteView(OrganizationScopedAPIView):
    def delete(self, request, org_id, group_id, member_id):
        organization = self.get_organization(request, org_id)
        require_can_manage_groups(request.user, organization)
        try:
            group = get_group(organization, group_id)
            remove_member_from_group(group, member_id)
        except Group.DoesNotExist as exc:
            raise NotFound("Group not found.") from exc
        except GroupMember.DoesNotExist as exc:
            raise NotFound("Group assignment not found.") from exc
        return Response(status=204)
