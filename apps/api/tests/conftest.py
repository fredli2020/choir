import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
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
        group=group, member_profile=section_leader_member_profile, role="leader"
    )
    return group
