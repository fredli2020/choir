from django.core.exceptions import ImproperlyConfigured
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from apps.accounts.clerk import verify_clerk_token
from apps.accounts.services import sync_user_from_clerk_claims


class ClerkJWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = authentication.get_authorization_header(request).split()
        if not auth_header:
            return None

        if auth_header[0].decode().lower() != self.keyword.lower():
            return None

        if len(auth_header) != 2:
            raise AuthenticationFailed(
                "Authorization header must be in the format 'Bearer <token>'."
            )

        token = auth_header[1].decode()

        try:
            claims = verify_clerk_token(token)
            user = sync_user_from_clerk_claims(claims)
        except ImproperlyConfigured as exc:
            raise AuthenticationFailed(str(exc)) from exc
        except ValueError as exc:
            raise AuthenticationFailed(str(exc)) from exc
        except Exception as exc:
            raise AuthenticationFailed("Unable to verify Clerk token.") from exc

        return (user, claims)
