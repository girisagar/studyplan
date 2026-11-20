from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError

from accounts.auth import jwt_auth, optional_auth
from notes.services import attach_note_counts
from .models import Chapter, Course, Tag, Topic
from .schemas import (
    CourseDetail,
    CourseRef,
    TagOut,
    TopicDescriptionIn,
    TopicDetail,
)

router = Router(tags=["curriculum"], auth=optional_auth)

TOPICS = Topic.objects.prefetch_related("tags", "resources")


@router.get("/courses", response=list[CourseRef])
def list_courses(request):
    return Course.objects.all()


@router.get("/courses/{course_id}", response=CourseDetail)
def get_course(request, course_id: int):
    """A course with its chapters (by week within the course) and topics."""
    course = get_object_or_404(
        Course.objects.prefetch_related(
            "resources",
            Prefetch(
                "chapters",
                Chapter.objects.prefetch_related(
                    "resources", Prefetch("topics", TOPICS)
                ),
            ),
        ),
        pk=course_id,
    )
    chapters = list(course.chapters.all())
    topics = [t for c in chapters for t in c.topics.all()]
    attach_note_counts([course, *chapters, *topics], request.user)
    return course


def _topic(request, topic_id):
    topic = get_object_or_404(
        TOPICS.select_related("chapter__course").prefetch_related("chapter__resources"),
        pk=topic_id,
    )
    attach_note_counts([topic, topic.chapter], request.user)
    topic.course = topic.chapter.course
    return topic


@router.get("/topics/{topic_id}", response=TopicDetail)
def get_topic(request, topic_id: int):
    return _topic(request, topic_id)


@router.put("/topics/{topic_id}/description", auth=jwt_auth, response=TopicDetail)
def set_topic_description(request, topic_id: int, payload: TopicDescriptionIn):
    """Replace a topic's rich-text description (needs curriculum.change_topic)."""
    if not request.user.has_perm("curriculum.change_topic"):
        raise HttpError(403, "You don't have permission to edit topics.")
    topic = get_object_or_404(Topic, pk=topic_id)
    topic.description = payload.description
    topic.save(update_fields=["description"])
    return _topic(request, topic_id)


@router.get("/tags", response=list[TagOut])
def list_tags(request):
    return Tag.objects.all()
