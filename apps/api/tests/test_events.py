from datetime import timedelta

import pytest

from apps.events.models import RSVP, AttendanceRecord, Event, EventAudience


@pytest.mark.django_db
def test_admin_can_create_event_with_selected_member_audience(
    api_client,
    admin_user,
    admin_membership,
    member_profile,
    unlinked_member_profile,
    now,
):
    api_client.force_authenticate(user=admin_user)

    response = api_client.post(
        f"/api/orgs/{admin_membership.organization_id}/events",
        {
            "title": "Chamber Ensemble Rehearsal",
            "description": "Prep for the spring concert",
            "type": Event.Type.REHEARSAL,
            "location": "Music Room",
            "start_at": now.isoformat(),
            "end_at": (now + timedelta(hours=2)).isoformat(),
            "timezone": "America/New_York",
            "is_all_day": False,
            "audience": {
                "audience_type": EventAudience.AudienceType.SELECTED_MEMBERS,
                "member_profile_ids": [str(member_profile.id), str(unlinked_member_profile.id)],
            },
        },
        format="json",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["title"] == "Chamber Ensemble Rehearsal"
    assert payload["audience"]["audience_type"] == EventAudience.AudienceType.SELECTED_MEMBERS
    assert payload["audience"]["member_count"] == 2


@pytest.mark.django_db
def test_invalid_event_dates_are_rejected(
    api_client,
    admin_user,
    admin_membership,
    now,
):
    api_client.force_authenticate(user=admin_user)

    response = api_client.post(
        f"/api/orgs/{admin_membership.organization_id}/events",
        {
            "title": "Broken Event",
            "type": Event.Type.MEETING,
            "start_at": now.isoformat(),
            "end_at": now.isoformat(),
            "timezone": "America/New_York",
            "is_all_day": False,
            "audience": {
                "audience_type": EventAudience.AudienceType.ALL_MEMBERS,
            },
        },
        format="json",
    )

    assert response.status_code == 400
    assert "end_at" in response.json()


@pytest.mark.django_db
def test_section_leader_can_view_event_list_but_cannot_create_event(
    api_client,
    section_leader_user,
    section_leader_membership,
    all_members_event,
    now,
):
    api_client.force_authenticate(user=section_leader_user)

    list_response = api_client.get(f"/api/orgs/{section_leader_membership.organization_id}/events")
    create_response = api_client.post(
        f"/api/orgs/{section_leader_membership.organization_id}/events",
        {
            "title": "Leader Planned Event",
            "type": Event.Type.MEETING,
            "start_at": now.isoformat(),
            "end_at": (now + timedelta(hours=1)).isoformat(),
            "timezone": "America/New_York",
            "is_all_day": False,
            "audience": {
                "audience_type": EventAudience.AudienceType.ALL_MEMBERS,
            },
        },
        format="json",
    )

    assert list_response.status_code == 200
    assert create_response.status_code == 403


@pytest.mark.django_db
def test_member_relevant_event_endpoints_only_return_targeted_events(
    api_client,
    member_user,
    member_membership,
    member_profile,
    all_members_event,
    section_event,
    selected_members_event,
):
    api_client.force_authenticate(user=member_user)

    relevant_response = api_client.get(
        f"/api/orgs/{member_membership.organization_id}/events/relevant"
    )
    upcoming_response = api_client.get(
        f"/api/orgs/{member_membership.organization_id}/events/upcoming"
    )

    assert relevant_response.status_code == 200
    assert upcoming_response.status_code == 200
    relevant_titles = {item["title"] for item in relevant_response.json()}
    upcoming_titles = {item["title"] for item in upcoming_response.json()}
    assert all_members_event.title in relevant_titles
    assert selected_members_event.title in relevant_titles
    assert section_event.title not in relevant_titles
    assert relevant_titles == upcoming_titles


@pytest.mark.django_db
def test_member_can_upsert_and_clear_rsvp(
    api_client,
    member_user,
    member_membership,
    member_profile,
    selected_members_event,
):
    api_client.force_authenticate(user=member_user)

    upsert_response = api_client.put(
        f"/api/orgs/{member_membership.organization_id}/events/{selected_members_event.id}/my-rsvp",
        {"status": RSVP.Status.YES, "note": "I will be there."},
        format="json",
    )
    clear_response = api_client.put(
        f"/api/orgs/{member_membership.organization_id}/events/{selected_members_event.id}/my-rsvp",
        {"status": RSVP.Status.NO_RESPONSE},
        format="json",
    )

    assert upsert_response.status_code == 200
    assert clear_response.status_code == 200
    assert not RSVP.objects.filter(
        event=selected_members_event,
        member_profile=member_profile,
    ).exists()


@pytest.mark.django_db
def test_event_rsvp_summary_includes_no_response_without_storing_rows(
    api_client,
    admin_user,
    admin_membership,
    admin_member_profile,
    section_leader_member_profile,
    member_profile,
    unlinked_member_profile,
    all_members_event,
):
    RSVP.objects.create(
        event=all_members_event,
        member_profile=member_profile,
        status=RSVP.Status.YES,
    )
    api_client.force_authenticate(user=admin_user)

    response = api_client.get(
        f"/api/orgs/{admin_membership.organization_id}/events/{all_members_event.id}/rsvps"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"] == {
        "yes": 1,
        "no": 0,
        "maybe": 0,
        "no_response": 3,
        "total_targeted": 4,
    }
    assert len(payload["responses"]) == 4


@pytest.mark.django_db
def test_section_leader_can_record_attendance_for_targeted_members(
    api_client,
    section_leader_user,
    section_leader_membership,
    section_leader_member_profile,
    section_event,
):
    api_client.force_authenticate(user=section_leader_user)

    response = api_client.put(
        f"/api/orgs/{section_leader_membership.organization_id}/events/{section_event.id}/attendance",
        {
            "records": [
                {
                    "member_profile_id": str(section_leader_member_profile.id),
                    "status": AttendanceRecord.Status.PRESENT,
                    "note": "On time",
                }
            ]
        },
        format="json",
    )

    assert response.status_code == 200
    attendance = AttendanceRecord.objects.get(
        event=section_event,
        member_profile=section_leader_member_profile,
    )
    assert attendance.status == AttendanceRecord.Status.PRESENT
    assert attendance.recorded_by_user == section_leader_user
    assert response.json()["summary"]["total_recorded"] == 1


@pytest.mark.django_db
def test_attendance_rejects_non_targeted_member(
    api_client,
    section_leader_user,
    section_leader_membership,
    section_event,
    member_profile,
):
    api_client.force_authenticate(user=section_leader_user)

    response = api_client.put(
        f"/api/orgs/{section_leader_membership.organization_id}/events/{section_event.id}/attendance",
        {
            "records": [
                {
                    "member_profile_id": str(member_profile.id),
                    "status": AttendanceRecord.Status.PRESENT,
                }
            ]
        },
        format="json",
    )

    assert response.status_code == 400
    assert "records" in response.json()
