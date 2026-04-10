from __future__ import annotations

from django.core.exceptions import PermissionDenied

from apps.organizations.models import OrganizationMembership


def list_active_memberships(user):
    if not getattr(user, "is_authenticated", False):
        return OrganizationMembership.objects.none()

    return (
        OrganizationMembership.objects.select_related("organization")
        .filter(user=user, status=OrganizationMembership.Status.ACTIVE)
        .order_by("organization__name")
    )


def get_default_membership(user) -> OrganizationMembership | None:
    return list_active_memberships(user).first()


def get_active_membership(user, organization) -> OrganizationMembership | None:
    if not getattr(user, "is_authenticated", False):
        return None

    return (
        OrganizationMembership.objects.select_related("organization")
        .filter(
            user=user,
            organization=organization,
            status=OrganizationMembership.Status.ACTIVE,
        )
        .first()
    )


def get_active_membership_for_org_id(user, organization_id) -> OrganizationMembership | None:
    if not getattr(user, "is_authenticated", False):
        return None

    return (
        OrganizationMembership.objects.select_related("organization")
        .filter(
            user=user,
            organization_id=organization_id,
            status=OrganizationMembership.Status.ACTIVE,
        )
        .first()
    )


def require_active_membership(user, organization_id) -> OrganizationMembership:
    membership = get_active_membership_for_org_id(user, organization_id)
    if membership is None:
        raise PermissionDenied("You do not have access to this organization.")
    return membership
