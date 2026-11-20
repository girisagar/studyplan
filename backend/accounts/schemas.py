from django.contrib.auth import get_user_model
from ninja import ModelSchema, Schema


class UserOut(ModelSchema):
    can_edit_topics: bool

    class Meta:
        model = get_user_model()
        fields = ["id", "username", "email", "is_staff", "date_joined"]

    @staticmethod
    def resolve_can_edit_topics(obj):
        return obj.has_perm("curriculum.change_topic")


class LoginIn(Schema):
    username: str
    password: str


class RegisterIn(Schema):
    username: str
    password1: str
    password2: str


class RefreshIn(Schema):
    refresh: str


class TokenPairOut(Schema):
    access: str
    refresh: str


class SessionOut(TokenPairOut):
    """Tokens plus the signed-in user, returned by login and register."""

    user: UserOut
