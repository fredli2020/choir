from functools import lru_cache

import jwt
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


@lru_cache
def get_jwks_client() -> jwt.PyJWKClient:
    if not settings.CLERK_JWKS_URL:
        raise ImproperlyConfigured("CLERK_JWKS_URL is not configured.")
    return jwt.PyJWKClient(settings.CLERK_JWKS_URL)


def verify_clerk_token(token: str) -> dict:
    if not settings.CLERK_ISSUER:
        raise ImproperlyConfigured("CLERK_ISSUER is not configured.")

    signing_key = get_jwks_client().get_signing_key_from_jwt(token)
    options = {"verify_aud": bool(settings.CLERK_AUDIENCE)}
    decode_kwargs = {
        "algorithms": ["RS256"],
        "issuer": settings.CLERK_ISSUER,
        "options": options,
    }

    if settings.CLERK_AUDIENCE:
        decode_kwargs["audience"] = settings.CLERK_AUDIENCE

    return jwt.decode(token, signing_key.key, **decode_kwargs)
