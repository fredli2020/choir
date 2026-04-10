from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.organizations.models import Organization, OrganizationMembership


class Command(BaseCommand):
    help = "Seed one sample organization with admin, section leader, and member users."

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
            },
            {
                "email": "leader@example.com",
                "name": "Section Leader",
                "auth_provider_id": "clerk_section_leader_seed",
                "role": OrganizationMembership.Role.SECTION_LEADER,
            },
            {
                "email": "member@example.com",
                "name": "Choir Member",
                "auth_provider_id": "clerk_member_seed",
                "role": OrganizationMembership.Role.MEMBER,
            },
        ]

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

        self.stdout.write(self.style.SUCCESS("Seeded sample organization and memberships."))
