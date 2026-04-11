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
WEB_APP_BASE_URL = "http://testserver:3000"
GOOGLE_OAUTH_CLIENT_ID = "google-client-id"
GOOGLE_OAUTH_CLIENT_SECRET = "google-client-secret"
GOOGLE_OAUTH_REDIRECT_URI = "http://testserver/api/integrations/google-calendar/oauth/callback"
GOOGLE_OAUTH_SCOPES = ["openid", "email", "https://www.googleapis.com/auth/calendar"]
GOOGLE_OAUTH_STATE_TTL_SECONDS = 900
GOOGLE_TOKEN_ENCRYPTION_KEY = "test-google-token-encryption-key"
