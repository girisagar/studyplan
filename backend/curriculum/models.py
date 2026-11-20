from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models.functions import Lower
from django.core.validators import MinValueValidator
from django_ckeditor_5.fields import CKEditor5Field
from library.models import Resource


class Course(models.Model):
    """A self-contained unit of study (often one textbook); roadmaps schedule courses."""

    notes = GenericRelation("notes.Note")
    name = models.CharField(max_length=255)
    description = CKEditor5Field(blank=True)
    resources = models.ManyToManyField(Resource, blank=True, related_name="courses")

    class Meta:
        ordering = ["name", "pk"]

    def __str__(self):
        return self.name


class Chapter(models.Model):
    notes = GenericRelation("notes.Note")
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="chapters"
    )
    week = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Week within the course in which this chapter is studied",
    )
    order = models.PositiveIntegerField(default=0, help_text="Order within the week")
    name = models.CharField(max_length=255)
    description = CKEditor5Field(blank=True)
    deliverable = models.TextField(blank=True)
    resources = models.ManyToManyField(Resource, blank=True, related_name="chapters")

    class Meta:
        ordering = ["course", "week", "order", "pk"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        ordering = [Lower("name")]
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_tag_name_ci",
                violation_error_message="A tag with this name already exists.",
            )
        ]

    def __str__(self):
        return self.name


class Topic(models.Model):
    notes = GenericRelation("notes.Note")
    chapter = models.ForeignKey(
        Chapter, on_delete=models.CASCADE, related_name="topics"
    )
    topic_name = models.CharField(max_length=255)
    description = CKEditor5Field(blank=True)
    total_time = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], help_text="Estimated hours"
    )
    order = models.PositiveIntegerField(default=0)
    tags = models.ManyToManyField(Tag, blank=True, related_name="topics")
    resources = models.ManyToManyField(Resource, blank=True, related_name="topics")

    def __str__(self):
        return self.topic_name

    class Meta:
        ordering = ["order", "pk"]
