import pytest

from apps.accounts.services import build_identity_from_claims, sync_user_from_clerk_claims
from apps.organizations.models import OrganizationMembership


@pytest.mark.django_db
def test_sync_user_from_clerk_claims_updates_existing_user(admin_user):
    claims = {
        "sub": "clerk_admin_test",
        "email": "admin@test.com",
        "name": "Updated Admin",
    }

    user = sync_user_from_clerk_claims(claims)

    assert user.id == admin_user.id
    assert user.name == "Updated Admin"


def test_build_identity_from_claims_requires_email():
    with pytest.raises(ValueError, match="email claim"):
        build_identity_from_claims({"sub": "clerk_user_123"})


@pytest.mark.django_db
def test_current_user_endpoint_uses_clerk_auth(monkeypatch, api_client):
    monkeypatch.setattr(
        "apps.accounts.authentication.verify_clerk_token",
        lambda token: {
            "sub": "clerk_api_user",
            "email": "api-user@test.com",
            "name": "API User",
        },
    )

    response = api_client.get("/api/me", HTTP_AUTHORIZATION="Bearer token")

    assert response.status_code == 200
    assert response.json()["email"] == "api-user@test.com"
    assert response.json()["auth_provider_id"] == "clerk_api_user"


@pytest.mark.django_db
def test_current_user_context_returns_org_and_permissions(
    monkeypatch,
    api_client,
    organization,
    admin_membership,
):
    monkeypatch.setattr(
        "apps.accounts.authentication.verify_clerk_token",
        lambda token: {
            "sub": admin_membership.user.auth_provider_id,
            "email": admin_membership.user.email,
            "name": admin_membership.user.name,
        },
    )

    response = api_client.get(
        f"/api/me/context?organization_id={organization.id}",
        HTTP_AUTHORIZATION="Bearer token",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["organization"]["id"] == str(organization.id)
    assert payload["membership"]["role"] == OrganizationMembership.Role.ADMIN
    assert payload["permissions"]["can_manage_google_calendar"] is True


@pytest.mark.django_db
def test_org_permissions_endpoint_rejects_non_member(
    monkeypatch, api_client, organization, outsider_user
):
    monkeypatch.setattr(
        "apps.accounts.authentication.verify_clerk_token",
        lambda token: {
            "sub": outsider_user.auth_provider_id,
            "email": outsider_user.email,
            "name": outsider_user.name,
        },
    )

    response = api_client.get(
        f"/api/orgs/{organization.id}/permissions",
        HTTP_AUTHORIZATION="Bearer token",
    )

    assert response.status_code == 403
