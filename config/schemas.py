"""Schema building blocks shared by every app's API."""

from typing import Annotated

from ninja import Schema
from pydantic import BeforeValidator

from notes.richtext import sanitize_description_html

# Stored rich text (CKEditor HTML), sanitized on the way out (nh3 allowlist in
# notes/richtext.py), so clients can render it as HTML.
RichHTML = Annotated[str, BeforeValidator(sanitize_description_html)]


class ErrorOut(Schema):
    detail: str


def absolute_url(context, url):
    """`url` made absolute for the current request (media lives on the API host)."""
    if not url:
        return None
    request = (context or {}).get("request")
    return request.build_absolute_uri(url) if request else url
