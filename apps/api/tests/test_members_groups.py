import pytest

from apps.members.models import Group, GroupMember, MemberProfile


@pytest.mark.django_db
def test_admin_can_list_members_with_filters(
    api_client,
    admin_user,
    admin_membership,
    admin_member_profile,
    member_profile,
    section_leader_member_profile,
):
    api_client.force_authenticate(user=admin_user)

    response = api_client.get(
        f"/api/orgs/{admin_membership.organization_id}/members",
        {"search": "maya", "voice_part": MemberProfile.VoicePart.SOPRANO},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["email"] == member_profile.email


@pytest.mark.django_db
def test_section_leader_can_view_members_but_cannot_create_them(
    api_client,
    section_leader_user,
    section_leader_membership,
    member_profile,
):
    api_client.force_authenticate(user=section_leader_user)

    list_response = api_client.get(f"/api/orgs/{section_leader_membership.organization_id}/members")
    create_response = api_client.post(
        f"/api/orgs/{section_leader_membership.organization_id}/members",
        {
            "first_name": "Rita",
            "last_name": "Reader",
            "email": "rita@example.com",
            "status": MemberProfile.Status.ACTIVE,
        },
        format="json",
    )

    assert list_response.status_code == 200
    assert create_response.status_code == 403


@pytest.mark.django_db
def test_member_detail_is_scoped_by_organization(
    api_client,
    admin_user,
    admin_membership,
    other_org_member_profile,
):
    api_client.force_authenticate(user=admin_user)

    response = api_client.get(
        f"/api/orgs/{admin_membership.organization_id}/members/{other_org_member_profile.id}"
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_directory_is_available_to_member_and_only_returns_active_members(
    api_client,
    member_user,
    member_membership,
    member_profile,
    inactive_member_profile,
    unlinked_member_profile,
):
    api_client.force_authenticate(user=member_user)

    response = api_client.get(f"/api/orgs/{member_membership.organization_id}/directory")

    assert response.status_code == 200
    emails = {entry["email"] for entry in response.json()}
    assert member_profile.email in emails
    assert unlinked_member_profile.email in emails
    assert inactive_member_profile.email not in emails


@pytest.mark.django_db
def test_my_profile_allows_limited_self_edit(
    api_client,
    member_user,
    member_membership,
    member_profile,
):
    api_client.force_authenticate(user=member_user)

    response = api_client.patch(
        f"/api/orgs/{member_membership.organization_id}/my-profile",
        {"phone": "555-9999", "first_name": "Maya Updated"},
        format="json",
    )

    assert response.status_code == 200
    member_profile.refresh_from_db()
    assert member_profile.phone == "555-9999"
    assert member_profile.first_name == "Maya Updated"


@pytest.mark.django_db
def test_member_cannot_access_member_admin_detail_endpoint(
    api_client,
    member_user,
    member_membership,
    member_profile,
):
    api_client.force_authenticate(user=member_user)

    response = api_client.get(
        f"/api/orgs/{member_membership.organization_id}/members/{member_profile.id}"
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_assign_and_remove_members_from_groups(
    api_client,
    admin_user,
    admin_membership,
    section_group,
    member_profile,
):
    api_client.force_authenticate(user=admin_user)

    create_response = api_client.post(
        f"/api/orgs/{admin_membership.organization_id}/groups/{section_group.id}/members",
        {"member_profile_id": str(member_profile.id), "role": "section member"},
        format="json",
    )
    delete_response = api_client.delete(
        f"/api/orgs/{admin_membership.organization_id}/groups/{section_group.id}/members/{member_profile.id}"
    )

    assert create_response.status_code == 201
    assert delete_response.status_code == 204
    assert not GroupMember.objects.filter(
        group=section_group, member_profile=member_profile
    ).exists()


@pytest.mark.django_db
def test_group_assignment_rejects_member_from_another_org(
    api_client,
    admin_user,
    admin_membership,
    section_group,
    other_org_member_profile,
):
    api_client.force_authenticate(user=admin_user)

    response = api_client.post(
        f"/api/orgs/{admin_membership.organization_id}/groups/{section_group.id}/members",
        {"member_profile_id": str(other_org_member_profile.id)},
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_group_list_supports_type_filter(
    api_client,
    section_leader_user,
    section_leader_membership,
    section_group,
):
    Group.objects.create(
        organization=section_leader_membership.organization,
        type=Group.Type.COMMITTEE,
        name="Planning Committee",
    )
    api_client.force_authenticate(user=section_leader_user)

    response = api_client.get(
        f"/api/orgs/{section_leader_membership.organization_id}/groups",
        {"type": Group.Type.SECTION},
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["name"] == section_group.name
