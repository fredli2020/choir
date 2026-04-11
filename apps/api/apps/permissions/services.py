from django.core.exceptions import PermissionDenied

from apps.organizations.models import Organization, OrganizationMembership
from apps.organizations.services import get_active_membership

ROLE_CAPABILITIES = {
    OrganizationMembership.Role.ADMIN: {
        "can_manage_members": True,
        "can_manage_groups": True,
        "can_view_members": True,
        "can_manage_events": True,
        "can_view_events": True,
        "can_view_relevant_events": True,
        "can_rsvp_to_events": True,
        "can_record_attendance": True,
        "can_send_messages": True,
        "can_manage_google_calendar": True,
        "can_view_directory": True,
        "can_self_edit_profile": True,
    },
    OrganizationMembership.Role.SECTION_LEADER: {
        "can_manage_members": False,
        "can_manage_groups": False,
        "can_view_members": True,
        "can_manage_events": False,
        "can_view_events": True,
        "can_view_relevant_events": True,
        "can_rsvp_to_events": True,
        "can_record_attendance": True,
        "can_send_messages": True,
        "can_manage_google_calendar": False,
        "can_view_directory": True,
        "can_self_edit_profile": True,
    },
    OrganizationMembership.Role.MEMBER: {
        "can_manage_members": False,
        "can_manage_groups": False,
        "can_view_members": False,
        "can_manage_events": False,
        "can_view_events": False,
        "can_view_relevant_events": True,
        "can_rsvp_to_events": True,
        "can_record_attendance": False,
        "can_send_messages": False,
        "can_manage_google_calendar": False,
        "can_view_directory": True,
        "can_self_edit_profile": True,
    },
}

EMPTY_CAPABILITIES = {
    "can_manage_members": False,
    "can_manage_groups": False,
    "can_view_members": False,
    "can_manage_events": False,
    "can_view_events": False,
    "can_view_relevant_events": False,
    "can_rsvp_to_events": False,
    "can_record_attendance": False,
    "can_send_messages": False,
    "can_manage_google_calendar": False,
    "can_view_directory": False,
    "can_self_edit_profile": False,
}


def get_membership_capabilities(membership: OrganizationMembership | None) -> dict[str, bool]:
    if membership is None or membership.status != OrganizationMembership.Status.ACTIVE:
        return EMPTY_CAPABILITIES.copy()
    return ROLE_CAPABILITIES[membership.role].copy()


def get_organization_capabilities(user, organization: Organization) -> dict[str, bool]:
    membership = get_active_membership(user, organization)
    return get_membership_capabilities(membership)


def has_capability(user, organization: Organization, capability: str) -> bool:
    return get_organization_capabilities(user, organization).get(capability, False)


def require_capability(
    user,
    organization: Organization,
    capability: str,
    message: str,
) -> None:
    if not has_capability(user, organization, capability):
        raise PermissionDenied(message)


def can_manage_members(user, organization: Organization) -> bool:
    return has_capability(user, organization, "can_manage_members")


def can_manage_groups(user, organization: Organization) -> bool:
    return has_capability(user, organization, "can_manage_groups")


def can_view_members(user, organization: Organization) -> bool:
    return has_capability(user, organization, "can_view_members")


def can_manage_events(user, organization: Organization) -> bool:
    return has_capability(user, organization, "can_manage_events")


def can_view_events(user, organization: Organization) -> bool:
    return has_capability(user, organization, "can_view_events")


def can_view_relevant_events(user, organization: Organization) -> bool:
    return has_capability(user, organization, "can_view_relevant_events")


def can_rsvp_to_events(user, organization: Organization) -> bool:
    return has_capability(user, organization, "can_rsvp_to_events")


def can_record_attendance(user, organization: Organization) -> bool:
    return has_capability(user, organization, "can_record_attendance")


def can_send_messages(user, organization: Organization) -> bool:
    return has_capability(user, organization, "can_send_messages")


def can_manage_google_calendar(user, organization: Organization) -> bool:
    return has_capability(user, organization, "can_manage_google_calendar")


def can_view_directory(user, organization: Organization) -> bool:
    return has_capability(user, organization, "can_view_directory")


def can_self_edit_profile(user, organization: Organization) -> bool:
    return has_capability(user, organization, "can_self_edit_profile")


def require_can_manage_members(user, organization: Organization) -> None:
    require_capability(
        user,
        organization,
        "can_manage_members",
        "You cannot manage members in this organization.",
    )


def require_can_manage_groups(user, organization: Organization) -> None:
    require_capability(
        user,
        organization,
        "can_manage_groups",
        "You cannot manage groups in this organization.",
    )


def require_can_view_members(user, organization: Organization) -> None:
    require_capability(
        user,
        organization,
        "can_view_members",
        "You cannot view member records in this organization.",
    )


def require_can_manage_events(user, organization: Organization) -> None:
    require_capability(
        user,
        organization,
        "can_manage_events",
        "You cannot manage events in this organization.",
    )


def require_can_view_events(user, organization: Organization) -> None:
    require_capability(
        user,
        organization,
        "can_view_events",
        "You cannot view all events in this organization.",
    )


def require_can_view_relevant_events(user, organization: Organization) -> None:
    require_capability(
        user,
        organization,
        "can_view_relevant_events",
        "You cannot view relevant events in this organization.",
    )


def require_can_rsvp_to_events(user, organization: Organization) -> None:
    require_capability(
        user,
        organization,
        "can_rsvp_to_events",
        "You cannot RSVP to events in this organization.",
    )


def require_can_record_attendance(user, organization: Organization) -> None:
    require_capability(
        user,
        organization,
        "can_record_attendance",
        "You cannot record attendance in this organization.",
    )


def require_can_view_directory(user, organization: Organization) -> None:
    require_capability(
        user,
        organization,
        "can_view_directory",
        "You cannot view the directory in this organization.",
    )


def require_can_send_messages(user, organization: Organization) -> None:
    require_capability(
        user,
        organization,
        "can_send_messages",
        "You cannot manage communications in this organization.",
    )


def require_can_self_edit_profile(user, organization: Organization) -> None:
    require_capability(
        user,
        organization,
        "can_self_edit_profile",
        "You cannot edit your profile in this organization.",
    )
