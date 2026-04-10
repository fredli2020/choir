from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.members.filters import GroupFilterSet, MemberProfileFilterSet
from apps.members.models import Group, GroupMember, MemberProfile
from apps.organizations.models import Organization


def _validate_member_profile_uniqueness(
    organization: Organization,
    email: str,
    user,
    current_member: MemberProfile | None = None,
) -> None:
    duplicate_email = MemberProfile.objects.filter(
        organization=organization,
        email__iexact=email,
    )
    if current_member is not None:
        duplicate_email = duplicate_email.exclude(id=current_member.id)
    if duplicate_email.exists():
        raise ValidationError(
            {"email": ["A member with this email already exists in the organization."]}
        )

    if user is None:
        return

    duplicate_user = MemberProfile.objects.filter(organization=organization, user=user)
    if current_member is not None:
        duplicate_user = duplicate_user.exclude(id=current_member.id)
    if duplicate_user.exists():
        raise ValidationError(
            {"user_id": ["This user is already linked to another member profile."]}
        )


def _validate_group_uniqueness(
    organization: Organization,
    group_type: str,
    name: str,
    current_group: Group | None = None,
) -> None:
    duplicate_group = Group.objects.filter(
        organization=organization,
        type=group_type,
        name__iexact=name,
    )
    if current_group is not None:
        duplicate_group = duplicate_group.exclude(id=current_group.id)
    if duplicate_group.exists():
        raise ValidationError({"name": ["A group with this type and name already exists."]})


def list_member_profiles(organization: Organization, filters: dict | None = None):
    queryset = MemberProfile.objects.filter(organization=organization).select_related("user")
    if filters is None:
        return queryset.order_by("last_name", "first_name", "email")

    filterset = MemberProfileFilterSet(filters, queryset=queryset)
    if not filterset.is_valid():
        raise ValidationError(filterset.errors)
    return filterset.qs.order_by("last_name", "first_name", "email")


def list_directory_members(organization: Organization, filters: dict | None = None):
    combined_filters = {**(filters or {}), "status": MemberProfile.Status.ACTIVE}
    return list_member_profiles(organization, combined_filters)


def get_member_profile(organization: Organization, member_id) -> MemberProfile:
    return MemberProfile.objects.select_related("user").get(
        id=member_id,
        organization=organization,
    )


@transaction.atomic
def create_member_profile(organization: Organization, data: dict) -> MemberProfile:
    user = data.pop("user_id", None)
    email = data["email"]
    _validate_member_profile_uniqueness(organization, email, user)
    return MemberProfile.objects.create(organization=organization, user=user, **data)


@transaction.atomic
def update_member_profile(member_profile: MemberProfile, data: dict) -> MemberProfile:
    user = data.pop("user_id", member_profile.user)
    email = data.get("email", member_profile.email)
    _validate_member_profile_uniqueness(
        member_profile.organization,
        email,
        user,
        current_member=member_profile,
    )
    member_profile.user = user
    for field, value in data.items():
        setattr(member_profile, field, value)
    member_profile.save()
    return member_profile


@transaction.atomic
def delete_member_profile(member_profile: MemberProfile) -> None:
    member_profile.delete()


def get_my_member_profile(organization: Organization, user) -> MemberProfile:
    try:
        return MemberProfile.objects.get(organization=organization, user=user)
    except MemberProfile.DoesNotExist as exc:
        raise PermissionDenied(
            "No member profile is linked to the current user in this organization."
        ) from exc


@transaction.atomic
def update_my_member_profile(member_profile: MemberProfile, data: dict) -> MemberProfile:
    for field, value in data.items():
        setattr(member_profile, field, value)
    member_profile.save(update_fields=[*data.keys(), "updated_at"])
    return member_profile


def list_groups(organization: Organization, filters: dict | None = None):
    queryset = Group.objects.filter(organization=organization).prefetch_related(
        "group_memberships__member_profile"
    )
    if filters is None:
        return queryset.order_by("type", "name")

    filterset = GroupFilterSet(filters, queryset=queryset)
    if not filterset.is_valid():
        raise ValidationError(filterset.errors)
    return filterset.qs.order_by("type", "name")


def get_group(organization: Organization, group_id) -> Group:
    return Group.objects.prefetch_related("group_memberships__member_profile").get(
        id=group_id,
        organization=organization,
    )


@transaction.atomic
def create_group(organization: Organization, data: dict) -> Group:
    _validate_group_uniqueness(organization, data["type"], data["name"])
    return Group.objects.create(organization=organization, **data)


@transaction.atomic
def update_group(group: Group, data: dict) -> Group:
    group_type = data.get("type", group.type)
    name = data.get("name", group.name)
    _validate_group_uniqueness(
        group.organization,
        group_type,
        name,
        current_group=group,
    )
    for field, value in data.items():
        setattr(group, field, value)
    group.save()
    return group


@transaction.atomic
def delete_group(group: Group) -> None:
    group.delete()


@transaction.atomic
def assign_member_to_group(
    group: Group,
    member_profile: MemberProfile,
    role: str | None = None,
) -> GroupMember:
    if member_profile.organization_id != group.organization_id:
        raise ValidationError("Member profile must belong to the same organization as the group.")

    assignment, created = GroupMember.objects.get_or_create(
        group=group,
        member_profile=member_profile,
        defaults={"role": role},
    )
    if not created:
        assignment.role = role
        assignment.save(update_fields=["role"])
    return assignment


@transaction.atomic
def remove_member_from_group(group: Group, member_profile_id) -> None:
    deleted, _ = GroupMember.objects.filter(
        group=group,
        member_profile_id=member_profile_id,
    ).delete()
    if deleted == 0:
        raise GroupMember.DoesNotExist("Group assignment not found.")
