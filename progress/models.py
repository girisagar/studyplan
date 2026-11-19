from django.conf import settings
from django.db import models
from django.db.models import Count
from django.utils import timezone

from curriculum.models import Topic
from roadmaps.models import RoadMap


class UserRoadMap(models.Model):
    """The user follows this roadmap (shows checkboxes and progress for it)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="roadmap_enrollments",
    )
    roadmap = models.ForeignKey(
        RoadMap, on_delete=models.PROTECT, related_name="enrollments"
    )
    started_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "roadmap"], name="unique_user_roadmap"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.roadmap.name}"


class UserTopicProgress(models.Model):
    """A completed topic. Shared by every roadmap that includes the topic's course;
    unchecking a topic deletes its row."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="topic_progress",
    )
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="progress")
    completed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "topic"], name="unique_user_topic_progress"
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.topic}"


def _progress(user, path, ids):
    """{id: {"completed", "total", "percent"}} counting topics grouped by `path`."""
    ids = list(ids)
    topics = Topic.objects.filter(**{f"{path}__in": ids})
    totals = dict(topics.values_list(path).annotate(n=Count("pk")))
    done = dict(
        topics.filter(progress__user=user).values_list(path).annotate(n=Count("pk"))
    )
    result = {}
    for pk in ids:
        total, completed = totals.get(pk, 0), done.get(pk, 0)
        result[pk] = {
            "completed": completed,
            "total": total,
            "percent": round(100 * completed / total) if total else 0,
        }
    return result


def roadmap_progress(user, roadmap_ids):
    """{roadmap_id: {"completed", "total", "percent"}} for the given roadmaps.

    The single source for progress numbers (pages, JSON endpoint, completion).
    """
    return _progress(user, "chapter__course__roadmap_links__roadmap_id", roadmap_ids)


def course_progress(user, course_ids):
    """{course_id: {"completed", "total", "percent"}} for the given courses."""
    return _progress(user, "chapter__course_id", course_ids)
