from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from django.db import models


class Resource(models.Model):
    """Any study material: an uploaded file (book, notes, code, ...), a URL, or both."""

    class Kind(models.TextChoices):
        BOOK = "book", "Book"
        PAPER = "paper", "Paper"
        PROBLEM_SET = "problem_set", "Problem set"
        SOLUTIONS = "solutions", "Solutions"
        NOTES = "notes", "Notes"
        CODE = "code", "Code"
        SLIDES = "slides", "Slides"
        VIDEO = "video", "Video"
        OTHER = "other", "Other"

    notes = GenericRelation("notes.Note")
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.BOOK)
    file = models.FileField(upload_to="resources/", blank=True)
    url = models.URLField(max_length=2000, blank=True)
    thumbnail = models.ImageField(
        upload_to="resource_thumbnails/", blank=True, null=True
    )

    class Meta:
        ordering = ["title", "pk"]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        if not self.file and not self.url:
            raise ValidationError("Upload a file or enter a URL (or both).")

    @property
    def is_pdf(self):
        """An uploaded PDF, which opens in the in-app reader."""
        return bool(self.file) and self.file.name.lower().endswith(".pdf")

    @property
    def href(self):
        """Where a link to this resource should point: the file if uploaded, else the URL."""
        return self.file.url if self.file else self.url
