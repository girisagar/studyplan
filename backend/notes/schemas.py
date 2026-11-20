from html import unescape

from django.utils.html import strip_tags
from ninja import ModelSchema, Schema
from pydantic import field_validator

from .models import Note
from .richtext import sanitize_note_html


class NoteIn(Schema):
    """`body` is rich text; it is sanitized to the note editor's formatting."""

    title: str = ""
    body: str

    @field_validator("title")
    @classmethod
    def clean_title(cls, value):
        value = value.strip()
        if len(value) > Note._meta.get_field("title").max_length:
            raise ValueError("Title is too long.")
        return value

    @field_validator("body")
    @classmethod
    def clean_body(cls, value):
        body = sanitize_note_html(value)
        if not unescape(strip_tags(body)).strip():
            raise ValueError("Write some text for your note.")
        return body


class NoteOut(ModelSchema):
    """A note; `body` is sanitized HTML."""

    app_label: str
    model: str

    class Meta:
        model = Note
        fields = ["id", "title", "body", "object_id", "created_at", "updated_at"]

    @staticmethod
    def resolve_app_label(obj):
        return obj.content_type.app_label

    @staticmethod
    def resolve_model(obj):
        return obj.content_type.model

    @staticmethod
    def resolve_body(obj):
        return sanitize_note_html(obj.body)


class NoteTarget(Schema):
    app_label: str
    model: str
    object_id: int
    title: str
    kind: str


class TargetNotesOut(Schema):
    target: NoteTarget
    notes: list[NoteOut]
