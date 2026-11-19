"""Authentication classes for the REST API.

The API authenticates only with JWT bearer tokens (never the Django session
cookie), so `request.user` inside an API operation is always the token's user
or AnonymousUser.
"""

from django.contrib.auth.models import AnonymousUser
from ninja_jwt.authentication import JWTAuth


class AnonymousAuth:
    """Accepts requests without credentials as AnonymousUser.

    Listed after JWTAuth for operations that also serve signed-out visitors: a
    valid token wins, a missing one falls through to here. An invalid or expired
    token still fails with 401 so the client knows to refresh it.
    """

    def __call__(self, request):
        if request.headers.get("Authorization"):
            return None
        request.user = AnonymousUser()
        return request.user


jwt_auth = JWTAuth()
optional_auth = [jwt_auth, AnonymousAuth()]
