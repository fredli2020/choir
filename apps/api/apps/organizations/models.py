from django.conf import settings
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class Organization(UUIDTimeStampedModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=120, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class OrganizationMembership(UUIDTimeStampedModel):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        SECTION_LEADER = "section_leader", "Section leader"
        MEMBER = "member", "Member"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INVITED = "invited", "Invited"
        SUSPENDED = "suspended", "Suspended"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organization_memberships",
    )
    role = models.CharField(max_length=32, choices=Role.choices)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["organization__name", "user__email"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "user"],
                name="unique_organization_membership",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.email} @ {self.organization.slug}"
