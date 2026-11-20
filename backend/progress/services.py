from django.shortcuts import get_object_or_404
from django.utils import timezone

from curriculum.models import Topic
from .models import UserRoadMap, UserTopicProgress, course_progress, roadmap_progress


def not_future(moment):
    """`moment` (or now if None), capped at now."""
    now = timezone.now()
    return min(moment, now) if moment else now


def set_completion(user, roadmap_id, topic_id, completed, completed_at=None):
    """Set (not toggle) a topic's completion; returns the new state with the
    roadmap's and the topic course's progress.

    Requires following the roadmap, and the topic must be part of it (Http404
    otherwise). Progress is per user and topic, so it shows in every roadmap
    that includes the topic.
    """
    get_object_or_404(UserRoadMap, user=user, roadmap_id=roadmap_id)
    topic = get_object_or_404(
        Topic.objects.filter(
            chapter__course__roadmap_links__roadmap_id=roadmap_id
        ).select_related("chapter"),
        pk=topic_id,
    )
    if completed:
        UserTopicProgress.objects.get_or_create(
            user=user, topic=topic, defaults={"completed_at": not_future(completed_at)}
        )
    else:
        UserTopicProgress.objects.filter(user=user, topic=topic).delete()
    course_id = topic.chapter.course_id
    return {
        "topic": topic,
        "completed": completed,
        "progress": roadmap_progress(user, [roadmap_id])[roadmap_id],
        "course": course_progress(user, [course_id])[course_id],
    }
