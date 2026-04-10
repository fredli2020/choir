from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.events.models import Event, EventAudience
from apps.members.models import Group, GroupMember, MemberProfile
from apps.organizations.models import Organization, OrganizationMembership


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def organization():
    return Organization.objects.create(name="Test Choir", slug="test-choir")


@pytest.fixture
def other_organization():
    return Organization.objects.create(name="Other Choir", slug="other-choir")


@pytest.fixture
def now():
    return timezone.now().replace(microsecond=0)


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="admin@test.com",
        name="Admin User",
        auth_provider_id="clerk_admin_test",
    )


@pytest.fixture
def section_leader_user():
    return User.objects.create_user(
        email="leader@test.com",
        name="Section Leader",
        auth_provider_id="clerk_section_leader_test",
    )


@pytest.fixture
def member_user():
    return User.objects.create_user(
        email="member@test.com",
        name="Member User",
        auth_provider_id="clerk_member_test",
    )


@pytest.fixture
def outsider_user():
    return User.objects.create_user(
        email="outsider@test.com",
        name="Outsider User",
        auth_provider_id="clerk_outsider_test",
    )


@pytest.fixture
def admin_membership(admin_user, organization):
    return OrganizationMembership.objects.create(
        organization=organization,
        user=admin_user,
        role=OrganizationMembership.Role.ADMIN,
        status=OrganizationMembership.Status.ACTIVE,
    )


@pytest.fixture
def section_leader_membership(section_leader_user, organization):
    return OrganizationMembership.objects.create(
        organization=organization,
        user=section_leader_user,
        role=OrganizationMembership.Role.SECTION_LEADER,
        status=OrganizationMembership.Status.ACTIVE,
    )


@pytest.fixture
def member_membership(member_user, organization):
    return OrganizationMembership.objects.create(
        organization=organization,
        user=member_user,
        role=OrganizationMembership.Role.MEMBER,
        status=OrganizationMembership.Status.ACTIVE,
    )


@pytest.fixture
def admin_member_profile(admin_user, organization):
    return MemberProfile.objects.create(
        organization=organization,
        user=admin_user,
        first_name="Ava",
        last_name="Director",
        email=admin_user.email,
        phone="555-0101",
        voice_part=MemberProfile.VoicePart.ALTO,
        status=MemberProfile.Status.ACTIVE,
    )


@pytest.fixture
def section_leader_member_profile(section_leader_user, organization):
    return MemberProfile.objects.create(
        organization=organization,
        user=section_leader_user,
        first_name="Theo",
        last_name="Leader",
        email=section_leader_user.email,
        phone="555-0102",
        voice_part=MemberProfile.VoicePart.TENOR,
        status=MemberProfile.Status.ACTIVE,
    )


@pytest.fixture
def member_profile(member_user, organization):
    return MemberProfile.objects.create(
        organization=organization,
        user=member_user,
        first_name="Maya",
        last_name="Singer",
        email=member_user.email,
        phone="555-0103",
        voice_part=MemberProfile.VoicePart.SOPRANO,
        status=MemberProfile.Status.ACTIVE,
    )


@pytest.fixture
def inactive_member_profile(organization):
    return MemberProfile.objects.create(
        organization=organization,
        first_name="Ian",
        last_name="Inactive",
        email="inactive@test.com",
        voice_part=MemberProfile.VoicePart.BASS,
        status=MemberProfile.Status.INACTIVE,
    )


@pytest.fixture
def unlinked_member_profile(organization):
    return MemberProfile.objects.create(
        organization=organization,
        first_name="Nina",
        last_name="Alto",
        email="nina@test.com",
        phone="555-0104",
        voice_part=MemberProfile.VoicePart.ALTO,
        status=MemberProfile.Status.ACTIVE,
    )


@pytest.fixture
def other_org_member_profile(other_organization):
    return MemberProfile.objects.create(
        organization=other_organization,
        first_name="Olivia",
        last_name="Other",
        email="olivia@other.com",
        voice_part=MemberProfile.VoicePart.ALTO,
        status=MemberProfile.Status.ACTIVE,
    )


@pytest.fixture
def section_group(organization, section_leader_member_profile):
    group = Group.objects.create(
        organization=organization,
        type=Group.Type.SECTION,
        name="Tenor Section",
        description="Tenor singers",
    )
    GroupMember.objects.create(
        group=group,
        member_profile=section_leader_member_profile,
        role="leader",
    )
    return group


@pytest.fixture
def all_members_event(organization, admin_user, now):
    event = Event.objects.create(
        organization=organization,
        title="Wednesday Rehearsal",
        description="Full choir rehearsal",
        type=Event.Type.REHEARSAL,
        location="Choir Room",
        start_at=now + timedelta(days=2),
        end_at=now + timedelta(days=2, hours=2),
        timezone="America/New_York",
        is_all_day=False,
        created_by_user=admin_user,
    )
    EventAudience.objects.create(
        event=event,
        audience_type=EventAudience.AudienceType.ALL_MEMBERS,
    )
    return event


@pytest.fixture
def section_event(organization, admin_user, now, section_group):
    event = Event.objects.create(
        organization=organization,
        title="Tenor Sectional",
        description="Focused sectional rehearsal",
        type=Event.Type.REHEARSAL,
        location="Practice Hall A",
        start_at=now + timedelta(days=3),
        end_at=now + timedelta(days=3, hours=1, minutes=30),
        timezone="America/New_York",
        is_all_day=False,
        created_by_user=admin_user,
    )
    EventAudience.objects.create(
        event=event,
        audience_type=EventAudience.AudienceType.GROUP,
        group=section_group,
    )
    return event


@pytest.fixture
def selected_members_event(
    organization,
    admin_user,
    now,
    member_profile,
    unlinked_member_profile,
):
    event = Event.objects.create(
        organization=organization,
        title="Small Ensemble Call",
        description="Extra ensemble prep",
        type=Event.Type.PERFORMANCE,
        location="Sanctuary",
        start_at=now + timedelta(days=5),
        end_at=now + timedelta(days=5, hours=2),
        timezone="America/New_York",
        is_all_day=False,
        created_by_user=admin_user,
    )
    EventAudience.objects.bulk_create(
        [
            EventAudience(
                event=event,
                audience_type=EventAudience.AudienceType.SELECTED_MEMBERS,
                member_profile=member_profile,
            ),
            EventAudience(
                event=event,
                audience_type=EventAudience.AudienceType.SELECTED_MEMBERS,
                member_profile=unlinked_member_profile,
            ),
        ]
    )
    return event
