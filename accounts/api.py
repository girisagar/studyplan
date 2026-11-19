"""Account endpoints: sign up, sign in/out with JWTs, and the current user.

Access tokens are short-lived; clients renew them with the refresh token.
Refreshing rotates the refresh token (the old one is blacklisted), and logout
blacklists the refresh token so it can't be used again.
"""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import update_last_login
from ninja import Router
from ninja.errors import ValidationError
from ninja_jwt.exceptions import TokenError
from ninja_jwt.settings import api_settings
from ninja_jwt.tokens import RefreshToken

from config.schemas import ErrorOut
from .schemas import LoginIn, RefreshIn, RegisterIn, SessionOut, TokenPairOut, UserOut

router = Router(tags=["auth"])


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def session_for(user):
    update_last_login(None, user)
    return {**issue_tokens(user), "user": user}


def form_errors(form):
    """A Django form's errors in django-ninja's 422 format."""
    return ValidationError(
        [
            {"loc": ["body", "payload", field], "msg": error, "type": "value_error"}
            for field, errors in form.errors.items()
            for error in errors
        ]
    )


@router.post("/register", auth=None, response={201: SessionOut})
def register(request, payload: RegisterIn):
    """Create an account (Django's password validators apply) and sign in."""
    form = UserCreationForm(data=payload.dict())
    if not form.is_valid():
        raise form_errors(form)
    return 201, session_for(form.save())


@router.post("/login", auth=None, response={200: SessionOut, 401: ErrorOut})
def login(request, payload: LoginIn):
    user = authenticate(request, username=payload.username, password=payload.password)
    if user is None:
        return 401, {"detail": "Invalid username or password."}
    return session_for(user)


@router.post("/refresh", auth=None, response={200: TokenPairOut, 401: ErrorOut})
def refresh(request, payload: RefreshIn):
    """Trade a refresh token for a new access token and a new refresh token."""
    try:
        token = RefreshToken(payload.refresh)
    except TokenError:
        return 401, {"detail": "Refresh token is invalid or expired."}
    user = (
        get_user_model()
        .objects.filter(
            **{api_settings.USER_ID_FIELD: token[api_settings.USER_ID_CLAIM]},
            is_active=True,
        )
        .first()
    )
    if user is None:
        return 401, {"detail": "Refresh token is invalid or expired."}
    token.blacklist()
    return issue_tokens(user)


@router.post("/logout", auth=None, response={204: None})
def logout(request, payload: RefreshIn):
    """Revoke the refresh token. Idempotent: an already invalid token is fine.
    Clients also discard their access token, which expires on its own."""
    try:
        RefreshToken(payload.refresh).blacklist()
    except TokenError:
        pass
    return 204, None


@router.get("/me", response=UserOut)
def me(request):
    return request.user
