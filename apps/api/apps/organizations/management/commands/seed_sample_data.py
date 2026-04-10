from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.members.models import Group, GroupMember, MemberProfile
from apps.organizations.models import Organization, OrganizationMembership


class Command(BaseCommand):
    help = "Seed one sample organization with users, member profiles, and groups."

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

        for sample in sample_users:
            user, _ = User.objects.update_or_create(
                email=sample["email"],
                defaults={
                    "name": sample["name"],
                    "auth_provider_id": sample["auth_provider_id"],
                    "is_active": True,
                },
            )
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

        self.stdout.write(
            self.style.SUCCESS(
                "Seeded sample organization and related sample memberships, profiles, and groups."
            )
        )
