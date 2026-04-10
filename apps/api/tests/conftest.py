import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMembership


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def organization():
    return Organization.objects.create(name="Test Choir", slug="test-choir")


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
