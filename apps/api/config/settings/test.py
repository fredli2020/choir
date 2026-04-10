from .base import *  # noqa: F403

DEBUG = False
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test.sqlite3",  # noqa: F405
    }
}
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
CLERK_JWKS_URL = "https://clerk.test/.well-known/jwks.json"
CLERK_ISSUER = "https://clerk.test"
CLERK_AUDIENCE = None
