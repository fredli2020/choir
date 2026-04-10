from apps.organizations.models import Organization, OrganizationMembership
from apps.organizations.services import get_active_membership

ROLE_CAPABILITIES = {
    OrganizationMembership.Role.ADMIN: {
        "can_manage_members": True,
        "can_manage_events": True,
        "can_record_attendance": True,
        "can_send_messages": True,
        "can_manage_google_calendar": True,
    },
    OrganizationMembership.Role.SECTION_LEADER: {
        "can_manage_members": True,
        "can_manage_events": True,
        "can_record_attendance": True,
        "can_send_messages": True,
        "can_manage_google_calendar": False,
    },
    OrganizationMembership.Role.MEMBER: {
        "can_manage_members": False,
        "can_manage_events": False,
        "can_record_attendance": False,
        "can_send_messages": False,
        "can_manage_google_calendar": False,
    },
}

EMPTY_CAPABILITIES = {
    "can_manage_members": False,
    "can_manage_events": False,
    "can_record_attendance": False,
    "can_send_messages": False,
    "can_manage_google_calendar": False,
}


def get_membership_capabilities(membership: OrganizationMembership | None) -> dict[str, bool]:
    if membership is None or membership.status != OrganizationMembership.Status.ACTIVE:
        return EMPTY_CAPABILITIES.copy()
    return ROLE_CAPABILITIES[membership.role].copy()


def get_organization_capabilities(user, organization: Organization) -> dict[str, bool]:
    membership = get_active_membership(user, organization)
    return get_membership_capabilities(membership)


def can_manage_members(user, organization: Organization) -> bool:
    return get_organization_capabilities(user, organization)["can_manage_members"]


def can_manage_events(user, organization: Organization) -> bool:
    return get_organization_capabilities(user, organization)["can_manage_events"]


def can_record_attendance(user, organization: Organization) -> bool:
    return get_organization_capabilities(user, organization)["can_record_attendance"]


def can_send_messages(user, organization: Organization) -> bool:
    return get_organization_capabilities(user, organization)["can_send_messages"]


def can_manage_google_calendar(user, organization: Organization) -> bool:
    return get_organization_capabilities(user, organization)["can_manage_google_calendar"]
