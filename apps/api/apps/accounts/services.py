from __future__ import annotations

from dataclasses import dataclass

from django.db import transaction

from apps.accounts.models import User
from apps.organizations.services import get_default_membership, require_active_membership
from apps.permissions.services import EMPTY_CAPABILITIES, get_membership_capabilities


@dataclass(frozen=True)
class ClerkIdentity:
    provider_id: str
    email: str
    name: str


@dataclass(frozen=True)
class CurrentUserContext:
    organization: object | None
    membership: object | None
    permissions: dict[str, bool]


def build_identity_from_claims(claims: dict) -> ClerkIdentity:
    provider_id = claims.get("sub")
    email = claims.get("email")
    full_name = (claims.get("name") or "").strip()
    given_name = (claims.get("given_name") or "").strip()
    family_name = (claims.get("family_name") or "").strip()
    name = (
        full_name or " ".join(part for part in [given_name, family_name] if part).strip() or email
    )

    if not provider_id:
        raise ValueError("Clerk token is missing the subject claim.")
    if not email:
        raise ValueError("Clerk token is missing the email claim.")

    return ClerkIdentity(provider_id=provider_id, email=email.lower(), name=name)


@transaction.atomic
def sync_user_from_clerk_claims(claims: dict) -> User:
    identity = build_identity_from_claims(claims)
    user = User.objects.filter(auth_provider_id=identity.provider_id).first()

    if user is None:
        user = User.objects.filter(email__iexact=identity.email).first()

        if (
            user is not None
            and user.auth_provider_id
            and user.auth_provider_id != identity.provider_id
        ):
            raise ValueError("Email is already linked to a different auth provider identity.")

        if user is None:
            user = User(email=identity.email)

    user.auth_provider_id = identity.provider_id
    user.email = identity.email
    user.name = identity.name
    user.is_active = True
    user.save()
    return user


def build_current_user_context(user, organization_id: str | None) -> CurrentUserContext:
    membership = (
        require_active_membership(user, organization_id)
        if organization_id
        else get_default_membership(user)
    )

    if membership is None:
        return CurrentUserContext(
            organization=None,
            membership=None,
            permissions=EMPTY_CAPABILITIES.copy(),
        )

    return CurrentUserContext(
        organization=membership.organization,
        membership=membership,
        permissions=get_membership_capabilities(membership),
    )
