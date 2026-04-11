from __future__ import annotations

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.events.filters import EventFilterSet
from apps.events.models import RSVP, AttendanceRecord, Event, EventAudience
from apps.integrations.google_calendar.services import (
    sync_deleted_event_to_google_calendar,
    sync_event_to_google_calendar,
)
from apps.members.models import Group, MemberProfile
from apps.organizations.models import Organization
from apps.permissions.services import can_view_events


def _normalize_optional_text(value):
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _validate_timezone_name(timezone_name: str) -> None:
    try:
        ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError as exc:
        raise ValidationError({"timezone": ["Enter a valid IANA timezone name."]}) from exc


def _validate_event_dates(data: dict) -> None:
    start_at = data["start_at"]
    end_at = data["end_at"]
    if end_at <= start_at:
        raise ValidationError({"end_at": ["End time must be after the start time."]})
    _validate_timezone_name(data["timezone"])


def _base_event_queryset():
    return Event.objects.select_related("created_by_user", "organization").prefetch_related(
        "audiences__group",
        "audiences__member_profile",
        "rsvps__member_profile",
        "attendance_records__member_profile",
        "attendance_records__recorded_by_user",
    )


def _apply_event_filters(queryset, filters: dict | None = None):
    if filters is None:
        return queryset.order_by("start_at", "title")

    filterset = EventFilterSet(filters, queryset=queryset)
    if not filterset.is_valid():
        raise ValidationError(filterset.errors)
    return filterset.qs.order_by("start_at", "title")


def _resolve_group(organization: Organization, group_id):
    return Group.objects.get(id=group_id, organization=organization)


def _resolve_member_profiles(organization: Organization, member_profile_ids: list):
    unique_ids = list(dict.fromkeys(str(member_id) for member_id in member_profile_ids))
    if len(unique_ids) != len(member_profile_ids):
        raise ValidationError(
            {"member_profile_ids": ["Duplicate member profiles are not allowed."]}
        )

    member_profiles = list(
        MemberProfile.objects.filter(
            organization=organization,
            id__in=unique_ids,
            status=MemberProfile.Status.ACTIVE,
        ).order_by("last_name", "first_name", "email")
    )
    if len(member_profiles) != len(unique_ids):
        raise ValidationError(
            {
                "member_profile_ids": [
                    "Every selected member must be active and in the organization."
                ]
            }
        )
    return member_profiles


def _resolve_audience_payload(organization: Organization, audience_data: dict) -> dict:
    audience_type = audience_data["audience_type"]
    group_id = audience_data.get("group_id")
    member_profile_ids = audience_data.get("member_profile_ids") or []

    if audience_type == EventAudience.AudienceType.ALL_MEMBERS:
        if group_id or member_profile_ids:
            raise ValidationError(
                {"audience": ["All-members audience cannot include a group or selected members."]}
            )
        return {"audience_type": audience_type, "group": None, "member_profiles": []}

    if audience_type == EventAudience.AudienceType.GROUP:
        if not group_id:
            raise ValidationError({"group_id": ["A group audience requires a group_id."]})
        if member_profile_ids:
            raise ValidationError(
                {"member_profile_ids": ["Group audience cannot include selected members."]}
            )
        try:
            group = _resolve_group(organization, group_id)
        except Group.DoesNotExist as exc:
            raise ValidationError({"group_id": ["Group not found in this organization."]}) from exc
        return {"audience_type": audience_type, "group": group, "member_profiles": []}

    if audience_type == EventAudience.AudienceType.SELECTED_MEMBERS:
        if group_id:
            raise ValidationError(
                {"group_id": ["Selected-members audience cannot include a group."]}
            )
        if not member_profile_ids:
            raise ValidationError(
                {"member_profile_ids": ["Selected-members audience requires at least one member."]}
            )
        member_profiles = _resolve_member_profiles(organization, member_profile_ids)
        return {
            "audience_type": audience_type,
            "group": None,
            "member_profiles": member_profiles,
        }

    raise ValidationError({"audience_type": ["Unsupported audience type."]})


def get_event_targeted_members_queryset(event: Event):
    audience_rows = list(event.audiences.all())
    if not audience_rows:
        return MemberProfile.objects.none()

    audience_type = audience_rows[0].audience_type
    if audience_type == EventAudience.AudienceType.ALL_MEMBERS:
        return MemberProfile.objects.filter(
            organization=event.organization,
            status=MemberProfile.Status.ACTIVE,
        ).order_by("last_name", "first_name", "email")

    if audience_type == EventAudience.AudienceType.GROUP:
        group = audience_rows[0].group
        return (
            MemberProfile.objects.filter(
                organization=event.organization,
                status=MemberProfile.Status.ACTIVE,
                group_memberships__group=group,
            )
            .distinct()
            .order_by("last_name", "first_name", "email")
        )

    member_ids = [row.member_profile_id for row in audience_rows if row.member_profile_id]
    return MemberProfile.objects.filter(
        organization=event.organization,
        status=MemberProfile.Status.ACTIVE,
        id__in=member_ids,
    ).order_by("last_name", "first_name", "email")


def get_event_targeted_members(event: Event) -> list[MemberProfile]:
    return list(get_event_targeted_members_queryset(event))


def get_linked_active_member_profile(organization: Organization, user) -> MemberProfile | None:
    if not getattr(user, "is_authenticated", False):
        return None
    return (
        MemberProfile.objects.filter(
            organization=organization,
            user=user,
            status=MemberProfile.Status.ACTIVE,
        )
        .select_related("organization", "user")
        .first()
    )


def is_event_relevant_to_member_profile(event: Event, member_profile: MemberProfile | None) -> bool:
    if member_profile is None:
        return False
    targeted_member_ids = {member.id for member in get_event_targeted_members(event)}
    return member_profile.id in targeted_member_ids


def list_events(organization: Organization, filters: dict | None = None):
    queryset = _base_event_queryset().filter(organization=organization)
    return _apply_event_filters(queryset, filters)


def list_relevant_events(organization: Organization, user, filters: dict | None = None):
    member_profile = get_linked_active_member_profile(organization, user)
    if member_profile is None:
        return Event.objects.none()

    queryset = (
        _base_event_queryset()
        .filter(organization=organization)
        .filter(
            Q(audiences__audience_type=EventAudience.AudienceType.ALL_MEMBERS)
            | Q(
                audiences__audience_type=EventAudience.AudienceType.GROUP,
                audiences__group__group_memberships__member_profile=member_profile,
            )
            | Q(
                audiences__audience_type=EventAudience.AudienceType.SELECTED_MEMBERS,
                audiences__member_profile=member_profile,
            )
        )
        .distinct()
    )
    return _apply_event_filters(queryset, filters)


def list_upcoming_relevant_events(organization: Organization, user, filters: dict | None = None):
    combined_filters = {**(filters or {}), "upcoming": True}
    return list_relevant_events(organization, user, combined_filters)


def get_event(organization: Organization, event_id) -> Event:
    return _base_event_queryset().get(id=event_id, organization=organization)


def _prepare_event_fields(data: dict) -> dict:
    fields = data.copy()
    fields["description"] = _normalize_optional_text(fields.get("description"))
    fields["location"] = _normalize_optional_text(fields.get("location"))
    fields["google_calendar_event_id"] = _normalize_optional_text(
        fields.get("google_calendar_event_id")
    )
    _validate_event_dates(fields)
    return fields


@transaction.atomic
def replace_event_audience(event: Event, audience_data: dict) -> Event:
    resolved_audience = _resolve_audience_payload(event.organization, audience_data)
    EventAudience.objects.filter(event=event).delete()

    audience_type = resolved_audience["audience_type"]
    if audience_type == EventAudience.AudienceType.ALL_MEMBERS:
        EventAudience.objects.create(event=event, audience_type=audience_type)
    elif audience_type == EventAudience.AudienceType.GROUP:
        EventAudience.objects.create(
            event=event,
            audience_type=audience_type,
            group=resolved_audience["group"],
        )
    else:
        EventAudience.objects.bulk_create(
            [
                EventAudience(
                    event=event,
                    audience_type=audience_type,
                    member_profile=member_profile,
                )
                for member_profile in resolved_audience["member_profiles"]
            ]
        )

    targeted_member_ids = [member.id for member in get_event_targeted_members(event)]
    RSVP.objects.filter(event=event).exclude(member_profile_id__in=targeted_member_ids).delete()
    AttendanceRecord.objects.filter(event=event).exclude(
        member_profile_id__in=targeted_member_ids
    ).delete()
    return get_event(event.organization, event.id)


@transaction.atomic
def _create_event_local(organization: Organization, created_by_user, data: dict) -> Event:
    payload = data.copy()
    audience_data = payload.pop("audience")
    event_fields = _prepare_event_fields(payload)
    event = Event.objects.create(
        organization=organization,
        created_by_user=created_by_user,
        **event_fields,
    )
    replace_event_audience(event, audience_data)
    return get_event(organization, event.id)


@transaction.atomic
def _update_event_local(event: Event, data: dict) -> Event:
    payload = data.copy()
    audience_data = payload.pop("audience", None)
    merged_fields = {
        "title": payload.get("title", event.title),
        "description": payload.get("description", event.description),
        "type": payload.get("type", event.type),
        "location": payload.get("location", event.location),
        "start_at": payload.get("start_at", event.start_at),
        "end_at": payload.get("end_at", event.end_at),
        "timezone": payload.get("timezone", event.timezone),
        "is_all_day": payload.get("is_all_day", event.is_all_day),
        "google_calendar_event_id": payload.get(
            "google_calendar_event_id", event.google_calendar_event_id
        ),
    }
    event_fields = _prepare_event_fields(merged_fields)
    for field, value in event_fields.items():
        setattr(event, field, value)
    event.save()

    if audience_data is not None:
        event = replace_event_audience(event, audience_data)
    return get_event(event.organization, event.id)


@transaction.atomic
def _delete_event_local(event: Event) -> dict:
    snapshot = {
        "organization": event.organization,
        "google_calendar_event_id": event.google_calendar_event_id,
    }
    event.delete()
    return snapshot


def create_event(organization: Organization, created_by_user, data: dict) -> Event:
    event = _create_event_local(organization, created_by_user, data)
    return sync_event_to_google_calendar(event)


def update_event(event: Event, data: dict) -> Event:
    event = _update_event_local(event, data)
    return sync_event_to_google_calendar(event)


def delete_event(event: Event) -> None:
    snapshot = _delete_event_local(event)
    sync_deleted_event_to_google_calendar(
        organization=snapshot["organization"],
        google_calendar_event_id=snapshot["google_calendar_event_id"],
    )


def get_event_audience_summary(event: Event) -> dict:
    audience_rows = list(event.audiences.all())
    if not audience_rows:
        return {
            "audience_type": None,
            "group": None,
            "selected_members": [],
            "member_count": 0,
        }

    audience_type = audience_rows[0].audience_type
    group = audience_rows[0].group if audience_type == EventAudience.AudienceType.GROUP else None
    selected_members = (
        [row.member_profile for row in audience_rows if row.member_profile is not None]
        if audience_type == EventAudience.AudienceType.SELECTED_MEMBERS
        else []
    )
    return {
        "audience_type": audience_type,
        "group": group,
        "selected_members": selected_members,
        "member_count": len(get_event_targeted_members(event)),
    }


def get_event_rsvp_summary(event: Event) -> dict:
    counts = {
        RSVP.Status.YES: 0,
        RSVP.Status.NO: 0,
        RSVP.Status.MAYBE: 0,
        RSVP.Status.NO_RESPONSE: 0,
    }
    targeted_members = get_event_targeted_members(event)
    rsvp_by_member_id = {
        rsvp.member_profile_id: rsvp
        for rsvp in event.rsvps.all()
        if rsvp.member_profile_id in {member.id for member in targeted_members}
    }
    for member in targeted_members:
        rsvp = rsvp_by_member_id.get(member.id)
        counts[rsvp.status if rsvp else RSVP.Status.NO_RESPONSE] += 1
    return {
        "yes": counts[RSVP.Status.YES],
        "no": counts[RSVP.Status.NO],
        "maybe": counts[RSVP.Status.MAYBE],
        "no_response": counts[RSVP.Status.NO_RESPONSE],
        "total_targeted": len(targeted_members),
    }


def get_event_attendance_summary(event: Event) -> dict:
    counts = {
        AttendanceRecord.Status.PRESENT: 0,
        AttendanceRecord.Status.ABSENT: 0,
        AttendanceRecord.Status.LATE: 0,
        AttendanceRecord.Status.EXCUSED: 0,
    }
    targeted_member_ids = {member.id for member in get_event_targeted_members(event)}
    total_recorded = 0
    for record in event.attendance_records.all():
        if record.member_profile_id not in targeted_member_ids:
            continue
        counts[record.status] += 1
        total_recorded += 1
    return {
        "present": counts[AttendanceRecord.Status.PRESENT],
        "absent": counts[AttendanceRecord.Status.ABSENT],
        "late": counts[AttendanceRecord.Status.LATE],
        "excused": counts[AttendanceRecord.Status.EXCUSED],
        "total_recorded": total_recorded,
        "total_targeted": len(targeted_member_ids),
    }


def list_event_rsvps(event: Event) -> list[dict]:
    targeted_members = get_event_targeted_members(event)
    rsvp_by_member_id = {rsvp.member_profile_id: rsvp for rsvp in event.rsvps.all()}
    rows = []
    for member in targeted_members:
        rsvp = rsvp_by_member_id.get(member.id)
        rows.append(
            {
                "member_profile": member,
                "status": rsvp.status if rsvp else RSVP.Status.NO_RESPONSE,
                "note": rsvp.note if rsvp else None,
                "responded_at": rsvp.responded_at if rsvp else None,
                "updated_at": rsvp.updated_at if rsvp else None,
            }
        )
    return rows


def list_attendance_roster(event: Event) -> list[dict]:
    targeted_members = get_event_targeted_members(event)
    rsvp_by_member_id = {rsvp.member_profile_id: rsvp for rsvp in event.rsvps.all()}
    attendance_by_member_id = {
        record.member_profile_id: record for record in event.attendance_records.all()
    }
    rows = []
    for member in targeted_members:
        rsvp = rsvp_by_member_id.get(member.id)
        attendance = attendance_by_member_id.get(member.id)
        rows.append(
            {
                "member_profile": member,
                "rsvp_status": rsvp.status if rsvp else RSVP.Status.NO_RESPONSE,
                "rsvp_note": rsvp.note if rsvp else None,
                "attendance_status": attendance.status if attendance else None,
                "attendance_note": attendance.note if attendance else None,
                "recorded_at": attendance.recorded_at if attendance else None,
                "recorded_by_user": attendance.recorded_by_user if attendance else None,
            }
        )
    return rows


def get_member_event_rsvp(event: Event, member_profile: MemberProfile | None) -> RSVP | None:
    if member_profile is None:
        return None
    return next(
        (rsvp for rsvp in event.rsvps.all() if rsvp.member_profile_id == member_profile.id),
        None,
    )


def get_event_for_user(organization: Organization, event_id, user) -> Event:
    event = get_event(organization, event_id)
    if can_view_events(user, organization):
        return event

    member_profile = get_linked_active_member_profile(organization, user)
    if is_event_relevant_to_member_profile(event, member_profile):
        return event
    raise PermissionDenied("You do not have access to this event.")


@transaction.atomic
def upsert_member_rsvp(event: Event, member_profile: MemberProfile, data: dict) -> RSVP | None:
    if not is_event_relevant_to_member_profile(event, member_profile):
        raise PermissionDenied("You can only RSVP to events relevant to your member profile.")

    status = data["status"]
    note = _normalize_optional_text(data.get("note"))
    if status == RSVP.Status.NO_RESPONSE:
        RSVP.objects.filter(event=event, member_profile=member_profile).delete()
        return None

    rsvp, _ = RSVP.objects.update_or_create(
        event=event,
        member_profile=member_profile,
        defaults={
            "status": status,
            "note": note,
            "responded_at": timezone.now(),
        },
    )
    return rsvp


def list_my_rsvp_responses(
    organization: Organization, user, filters: dict | None = None
) -> list[dict]:
    member_profile = get_linked_active_member_profile(organization, user)
    if member_profile is None:
        return []

    rows = []
    for event in list_relevant_events(organization, user, filters):
        rsvp = get_member_event_rsvp(event, member_profile)
        rows.append(
            {
                "event": event,
                "rsvp": rsvp,
                "status": rsvp.status if rsvp else RSVP.Status.NO_RESPONSE,
            }
        )
    return rows


@transaction.atomic
def bulk_upsert_attendance(event: Event, recorded_by_user, records: list[dict]) -> Event:
    member_profile_ids = [str(record["member_profile_id"]) for record in records]
    if len(member_profile_ids) != len(set(member_profile_ids)):
        raise ValidationError({"records": ["Duplicate member_profile_id values are not allowed."]})

    member_profiles = {
        str(member.id): member
        for member in MemberProfile.objects.filter(
            organization=event.organization,
            id__in=member_profile_ids,
        )
    }
    if len(member_profiles) != len(member_profile_ids):
        raise ValidationError(
            {"records": ["Every attendance record must reference a member in the organization."]}
        )

    targeted_member_ids = {str(member.id) for member in get_event_targeted_members(event)}
    for record in records:
        member_profile_id = str(record["member_profile_id"])
        if member_profile_id not in targeted_member_ids:
            raise ValidationError(
                {"records": ["Attendance can only be recorded for targeted event members."]}
            )

    recorded_at = timezone.now()
    for record in records:
        member_profile = member_profiles[str(record["member_profile_id"])]
        AttendanceRecord.objects.update_or_create(
            event=event,
            member_profile=member_profile,
            defaults={
                "status": record["status"],
                "note": _normalize_optional_text(record.get("note")),
                "recorded_by_user": recorded_by_user,
                "recorded_at": recorded_at,
            },
        )
    return get_event(event.organization, event.id)
