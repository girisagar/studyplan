from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.core.validators import MinValueValidator
from django_ckeditor_5.fields import CKEditor5Field
from curriculum.models import Course


class RoadMap(models.Model):
    """A study path: courses scheduled on a shared week timeline (they may overlap)."""

    notes = GenericRelation("notes.Note")
    name = models.CharField(max_length=255)
    description = CKEditor5Field(blank=True)
    courses = models.ManyToManyField(
        Course, through="RoadMapCourse", related_name="roadmaps"
    )

    def __str__(self):
        return self.name


class RoadMapCourse(models.Model):
    """Places a course on a roadmap. Chapter week w of the course falls on roadmap
    week start_week + w - 1, so courses with overlapping ranges run in parallel."""

    roadmap = models.ForeignKey(
        RoadMap, on_delete=models.CASCADE, related_name="course_links"
    )
    course = models.ForeignKey(
        Course, on_delete=models.PROTECT, related_name="roadmap_links"
    )
    order = models.PositiveIntegerField(
        default=0, help_text="Order among courses that share a week"
    )
    start_week = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1)]
    )

    class Meta:
        ordering = ["start_week", "order", "pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["roadmap", "course"], name="unique_roadmap_course"
            )
        ]

    def __str__(self):
        return f"{self.roadmap}: {self.course} (from week {self.start_week})"
