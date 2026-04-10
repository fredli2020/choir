import pytest

from apps.organizations.models import OrganizationMembership
from apps.permissions.services import (
    can_manage_events,
    can_manage_google_calendar,
    can_manage_groups,
    can_manage_members,
    can_record_attendance,
    can_rsvp_to_events,
    can_send_messages,
    can_view_directory,
    can_view_events,
    can_view_members,
    can_view_relevant_events,
)


@pytest.mark.django_db
def test_admin_permissions_grant_full_access(organization, admin_membership):
    user = admin_membership.user

    assert can_manage_members(user, organization) is True
    assert can_manage_groups(user, organization) is True
    assert can_view_members(user, organization) is True
    assert can_manage_events(user, organization) is True
    assert can_view_events(user, organization) is True
    assert can_view_relevant_events(user, organization) is True
    assert can_rsvp_to_events(user, organization) is True
    assert can_record_attendance(user, organization) is True
    assert can_send_messages(user, organization) is True
    assert can_manage_google_calendar(user, organization) is True
    assert can_view_directory(user, organization) is True


@pytest.mark.django_db
def test_section_leader_permissions_can_view_events_but_not_manage_them(
    organization,
    section_leader_membership,
):
    user = section_leader_membership.user

    assert can_manage_members(user, organization) is False
    assert can_manage_groups(user, organization) is False
    assert can_view_members(user, organization) is True
    assert can_manage_events(user, organization) is False
    assert can_view_events(user, organization) is True
    assert can_view_relevant_events(user, organization) is True
    assert can_rsvp_to_events(user, organization) is True
    assert can_record_attendance(user, organization) is True
    assert can_send_messages(user, organization) is True
    assert can_manage_google_calendar(user, organization) is False
    assert can_view_directory(user, organization) is True


@pytest.mark.django_db
def test_member_permissions_are_relevant_event_and_directory_only(
    organization,
    member_membership,
):
    user = member_membership.user

    assert can_manage_members(user, organization) is False
    assert can_manage_groups(user, organization) is False
    assert can_view_members(user, organization) is False
    assert can_manage_events(user, organization) is False
    assert can_view_events(user, organization) is False
    assert can_view_relevant_events(user, organization) is True
    assert can_rsvp_to_events(user, organization) is True
    assert can_record_attendance(user, organization) is False
    assert can_send_messages(user, organization) is False
    assert can_manage_google_calendar(user, organization) is False
    assert can_view_directory(user, organization) is True


@pytest.mark.django_db
def test_suspended_membership_has_no_permissions(admin_user, organization):
    OrganizationMembership.objects.create(
        organization=organization,
        user=admin_user,
        role=OrganizationMembership.Role.ADMIN,
        status=OrganizationMembership.Status.SUSPENDED,
    )

    assert can_manage_members(admin_user, organization) is False
    assert can_view_events(admin_user, organization) is False
    assert can_view_relevant_events(admin_user, organization) is False
    assert can_rsvp_to_events(admin_user, organization) is False
    assert can_view_directory(admin_user, organization) is False
