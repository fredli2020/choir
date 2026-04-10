from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.core.models import UUIDCreatedModel, UUIDTimeStampedModel
from apps.organizations.models import Organization


class MemberProfile(UUIDTimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    class VoicePart(models.TextChoices):
        SOPRANO = "soprano", "Soprano"
        ALTO = "alto", "Alto"
        TENOR = "tenor", "Tenor"
        BASS = "bass", "Bass"
        BARITONE = "baritone", "Baritone"
        MEZZO_SOPRANO = "mezzo_soprano", "Mezzo-soprano"
        CONTRALTO = "contralto", "Contralto"
        OTHER = "other", "Other"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="member_profiles",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="member_profiles",
    )
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, null=True, blank=True)
    voice_part = models.CharField(
        max_length=32,
        choices=VoicePart.choices,
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    notes = models.TextField(null=True, blank=True)
    joined_at = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["last_name", "first_name", "email"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "email"],
                name="unique_member_email_per_organization",
            ),
            models.UniqueConstraint(
                fields=["organization", "user"],
                condition=Q(user__isnull=False),
                name="unique_member_user_per_organization",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Group(UUIDTimeStampedModel):
    class Type(models.TextChoices):
        SECTION = "section", "Section"
        COMMITTEE = "committee", "Committee"
        ENSEMBLE = "ensemble", "Ensemble"
        OTHER = "other", "Other"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="groups",
    )
    type = models.CharField(max_length=24, choices=Type.choices)
    name = models.CharField(max_length=120)
    description = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ["type", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "type", "name"],
                name="unique_group_name_per_org_and_type",
            )
        ]

    def __str__(self) -> str:
        return self.name


class GroupMember(UUIDCreatedModel):
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="group_memberships",
    )
    member_profile = models.ForeignKey(
        MemberProfile,
        on_delete=models.CASCADE,
        related_name="group_memberships",
    )
    role = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        ordering = ["group__name", "member_profile__last_name", "member_profile__first_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["group", "member_profile"],
                name="unique_group_member_assignment",
            )
        ]

    def __str__(self) -> str:
        return f"{self.member_profile} in {self.group}"
