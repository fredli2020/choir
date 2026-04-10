from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.events.models import RSVP, AttendanceRecord, Event
from apps.events.services import replace_event_audience
from apps.members.models import Group, GroupMember, MemberProfile
from apps.organizations.models import Organization, OrganizationMembership


class Command(BaseCommand):
    help = "Seed one sample organization with users, member profiles, groups, and events."

    @transaction.atomic
    def handle(self, *args, **options):
        organization, _ = Organization.objects.update_or_create(
            slug="sample-choir",
            defaults={"name": "Sample Choir"},
        )

        sample_users = [
            {
                "email": "admin@example.com",
                "name": "Admin User",
                "auth_provider_id": "clerk_admin_seed",
                "role": OrganizationMembership.Role.ADMIN,
                "member": {
                    "first_name": "Ava",
                    "last_name": "Director",
                    "voice_part": MemberProfile.VoicePart.ALTO,
                    "phone": "555-0101",
                },
            },
            {
                "email": "leader@example.com",
                "name": "Section Leader",
                "auth_provider_id": "clerk_section_leader_seed",
                "role": OrganizationMembership.Role.SECTION_LEADER,
                "member": {
                    "first_name": "Theo",
                    "last_name": "Leader",
                    "voice_part": MemberProfile.VoicePart.TENOR,
                    "phone": "555-0102",
                },
            },
            {
                "email": "member@example.com",
                "name": "Choir Member",
                "auth_provider_id": "clerk_member_seed",
                "role": OrganizationMembership.Role.MEMBER,
                "member": {
                    "first_name": "Maya",
                    "last_name": "Singer",
                    "voice_part": MemberProfile.VoicePart.SOPRANO,
                    "phone": "555-0103",
                },
            },
        ]

        seeded_member_profiles = {}
        seeded_users = {}

        for sample in sample_users:
            user, _ = User.objects.update_or_create(
                email=sample["email"],
                defaults={
                    "name": sample["name"],
                    "auth_provider_id": sample["auth_provider_id"],
                    "is_active": True,
                },
            )
            seeded_users[sample["email"]] = user
            OrganizationMembership.objects.update_or_create(
                organization=organization,
                user=user,
                defaults={
                    "role": sample["role"],
                    "status": OrganizationMembership.Status.ACTIVE,
                },
            )
            member_profile, _ = MemberProfile.objects.update_or_create(
                organization=organization,
                email=sample["email"],
                defaults={
                    "user": user,
                    "first_name": sample["member"]["first_name"],
                    "last_name": sample["member"]["last_name"],
                    "phone": sample["member"]["phone"],
                    "voice_part": sample["member"]["voice_part"],
                    "status": MemberProfile.Status.ACTIVE,
                    "joined_at": date(2025, 9, 1),
                },
            )
            seeded_member_profiles[sample["email"]] = member_profile

        extra_members = [
            {
                "first_name": "Nina",
                "last_name": "Alto",
                "email": "nina.alto@example.com",
                "phone": "555-0104",
                "voice_part": MemberProfile.VoicePart.ALTO,
            },
            {
                "first_name": "Ben",
                "last_name": "Bass",
                "email": "ben.bass@example.com",
                "phone": "555-0105",
                "voice_part": MemberProfile.VoicePart.BASS,
            },
            {
                "first_name": "Lena",
                "last_name": "Committee",
                "email": "lena.committee@example.com",
                "phone": "555-0106",
                "voice_part": MemberProfile.VoicePart.MEZZO_SOPRANO,
            },
        ]

        for extra_member in extra_members:
            member_profile, _ = MemberProfile.objects.update_or_create(
                organization=organization,
                email=extra_member["email"],
                defaults={
                    **extra_member,
                    "status": MemberProfile.Status.ACTIVE,
                    "joined_at": date(2025, 10, 1),
                },
            )
            seeded_member_profiles[extra_member["email"]] = member_profile

        seeded_groups = {}
        groups = [
            {
                "type": Group.Type.SECTION,
                "name": "Soprano Section",
                "description": "Primary soprano section roster.",
                "members": [
                    ("member@example.com", "section member"),
                ],
            },
            {
                "type": Group.Type.SECTION,
                "name": "Tenor Section",
                "description": "Primary tenor section roster.",
                "members": [
                    ("leader@example.com", "section leader"),
                ],
            },
            {
                "type": Group.Type.COMMITTEE,
                "name": "Worship Planning Committee",
                "description": "Plans seasonal liturgy and music flow.",
                "members": [
                    ("admin@example.com", "chair"),
                    ("lena.committee@example.com", "member"),
                ],
            },
            {
                "type": Group.Type.ENSEMBLE,
                "name": "Chamber Ensemble",
                "description": "Small ensemble for special services.",
                "members": [
                    ("admin@example.com", "director"),
                    ("member@example.com", "soprano"),
                    ("nina.alto@example.com", "alto"),
                    ("leader@example.com", "tenor"),
                    ("ben.bass@example.com", "bass"),
                ],
            },
        ]

        for group_data in groups:
            group, _ = Group.objects.update_or_create(
                organization=organization,
                type=group_data["type"],
                name=group_data["name"],
                defaults={"description": group_data["description"]},
            )
            seeded_groups[group_data["name"]] = group
            desired_member_ids = set()
            for email, role in group_data["members"]:
                member_profile = seeded_member_profiles[email]
                desired_member_ids.add(member_profile.id)
                GroupMember.objects.update_or_create(
                    group=group,
                    member_profile=member_profile,
                    defaults={"role": role},
                )
            GroupMember.objects.filter(group=group).exclude(
                member_profile_id__in=desired_member_ids
            ).delete()

        eastern = ZoneInfo("America/New_York")
        sample_events = [
            {
                "title": "Midweek Rehearsal",
                "description": "Full choir rehearsal for Sunday service music.",
                "type": Event.Type.REHEARSAL,
                "location": "Choir Room",
                "start_at": datetime(2026, 5, 6, 19, 0, tzinfo=eastern),
                "end_at": datetime(2026, 5, 6, 21, 0, tzinfo=eastern),
                "timezone": "America/New_York",
                "is_all_day": False,
                "created_by_user": seeded_users["admin@example.com"],
                "audience": {"audience_type": "all_members"},
            },
            {
                "title": "Spring Concert",
                "description": "Performance call for the chamber ensemble.",
                "type": Event.Type.PERFORMANCE,
                "location": "Main Sanctuary",
                "start_at": datetime(2026, 5, 10, 15, 0, tzinfo=eastern),
                "end_at": datetime(2026, 5, 10, 17, 0, tzinfo=eastern),
                "timezone": "America/New_York",
                "is_all_day": False,
                "created_by_user": seeded_users["admin@example.com"],
                "audience": {
                    "audience_type": "group",
                    "group_id": seeded_groups["Chamber Ensemble"].id,
                },
            },
            {
                "title": "Worship Planning Meeting",
                "description": "Monthly planning meeting for liturgy and music flow.",
                "type": Event.Type.MEETING,
                "location": "Conference Room",
                "start_at": datetime(2026, 5, 12, 18, 30, tzinfo=eastern),
                "end_at": datetime(2026, 5, 12, 19, 30, tzinfo=eastern),
                "timezone": "America/New_York",
                "is_all_day": False,
                "created_by_user": seeded_users["leader@example.com"],
                "audience": {
                    "audience_type": "group",
                    "group_id": seeded_groups["Worship Planning Committee"].id,
                },
            },
            {
                "title": "Soloist Call",
                "description": "Extra coaching session for selected singers.",
                "type": Event.Type.OTHER,
                "location": "Music Office",
                "start_at": datetime(2026, 5, 8, 17, 30, tzinfo=eastern),
                "end_at": datetime(2026, 5, 8, 18, 30, tzinfo=eastern),
                "timezone": "America/New_York",
                "is_all_day": False,
                "created_by_user": seeded_users["admin@example.com"],
                "audience": {
                    "audience_type": "selected_members",
                    "member_profile_ids": [
                        seeded_member_profiles["member@example.com"].id,
                        seeded_member_profiles["nina.alto@example.com"].id,
                    ],
                },
            },
        ]

        seeded_events = {}
        for event_data in sample_events:
            event, _ = Event.objects.update_or_create(
                organization=organization,
                title=event_data["title"],
                defaults={
                    "description": event_data["description"],
                    "type": event_data["type"],
                    "location": event_data["location"],
                    "start_at": event_data["start_at"],
                    "end_at": event_data["end_at"],
                    "timezone": event_data["timezone"],
                    "is_all_day": event_data["is_all_day"],
                    "created_by_user": event_data["created_by_user"],
                },
            )
            replace_event_audience(event, event_data["audience"])
            seeded_events[event.title] = event

        rsvp_rows = [
            ("Midweek Rehearsal", "admin@example.com", RSVP.Status.YES, "Running warmups."),
            ("Midweek Rehearsal", "leader@example.com", RSVP.Status.YES, None),
            (
                "Midweek Rehearsal",
                "member@example.com",
                RSVP.Status.MAYBE,
                "Might be a few minutes late.",
            ),
            ("Spring Concert", "member@example.com", RSVP.Status.YES, None),
            ("Spring Concert", "ben.bass@example.com", RSVP.Status.NO, "Out of town."),
            ("Soloist Call", "member@example.com", RSVP.Status.YES, "Confirmed."),
            ("Soloist Call", "nina.alto@example.com", RSVP.Status.MAYBE, None),
        ]

        for event_title, email, status, note in rsvp_rows:
            RSVP.objects.update_or_create(
                event=seeded_events[event_title],
                member_profile=seeded_member_profiles[email],
                defaults={
                    "status": status,
                    "note": note,
                    "responded_at": timezone.now(),
                },
            )

        attendance_rows = [
            (
                "Midweek Rehearsal",
                "admin@example.com",
                AttendanceRecord.Status.PRESENT,
                "Led sectionals.",
                seeded_users["admin@example.com"],
            ),
            (
                "Midweek Rehearsal",
                "leader@example.com",
                AttendanceRecord.Status.PRESENT,
                None,
                seeded_users["leader@example.com"],
            ),
            (
                "Spring Concert",
                "member@example.com",
                AttendanceRecord.Status.PRESENT,
                "Checked in early.",
                seeded_users["leader@example.com"],
            ),
            (
                "Spring Concert",
                "nina.alto@example.com",
                AttendanceRecord.Status.LATE,
                "Traffic delay.",
                seeded_users["leader@example.com"],
            ),
        ]

        for event_title, email, status, note, recorded_by_user in attendance_rows:
            AttendanceRecord.objects.update_or_create(
                event=seeded_events[event_title],
                member_profile=seeded_member_profiles[email],
                defaults={
                    "status": status,
                    "note": note,
                    "recorded_by_user": recorded_by_user,
                    "recorded_at": timezone.now(),
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded sample organization with profiles, groups, events, RSVPs, and attendance."
            )
        )
