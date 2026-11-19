"""Roadmaps, their overview and the course player. Open to signed-out
visitors; with a token, responses include the user's progress and notes."""

from django.shortcuts import get_object_or_404
from ninja import Router

from accounts.auth import optional_auth
from .models import RoadMap
from .schemas import CoursePlayer, RoadMapDetail, RoadMapListItem, TopicPanel
from .services import (
    course_for_topic,
    course_for_week,
    course_player,
    roadmap_cards,
    roadmap_overview,
)

router = Router(tags=["roadmaps"], auth=optional_auth)


@router.get("", response=list[RoadMapListItem])
def list_roadmaps(request):
    return roadmap_cards(request.user)


@router.get("/{roadmap_id}", response=RoadMapDetail)
def get_roadmap(request, roadmap_id: int):
    """Overview: courses in timeline order with per-course progress and state,
    the week-by-week outline, next topic and totals."""
    roadmap = get_object_or_404(RoadMap, pk=roadmap_id)
    data = roadmap_overview(roadmap, request.user)
    return {
        **{f: getattr(roadmap, f) for f in ("id", "name", "description")},
        "note_count": roadmap.note_count,
        **data,
    }


@router.get("/{roadmap_id}/courses/{course_id}", response=CoursePlayer)
def get_course_player(
    request,
    roadmap_id: int,
    course_id: int,
    week: int | None = None,
    topic: int | None = None,
):
    """The course player. Without `topic` it resumes at the first unfinished
    topic (of `week`, a roadmap week, if given). Weeks are on the roadmap
    timeline; previous/next stay within the course."""
    roadmap = get_object_or_404(RoadMap, pk=roadmap_id)
    return course_player(roadmap, course_id, request.user, week, topic)


@router.get("/{roadmap_id}/courses/{course_id}/topics/{topic_id}", response=TopicPanel)
def get_topic_panel(request, roadmap_id: int, course_id: int, topic_id: int):
    """Only the player's content pane for a topic (no outline)."""
    roadmap = get_object_or_404(RoadMap, pk=roadmap_id)
    return course_player(roadmap, course_id, request.user, topic_pk=topic_id)


@router.get("/{roadmap_id}/weeks/{week}", response=CoursePlayer)
def get_week(request, roadmap_id: int, week: int):
    """The player of the first course scheduled in this roadmap week."""
    roadmap = get_object_or_404(RoadMap, pk=roadmap_id)
    course_id = course_for_week(roadmap, week)
    return course_player(roadmap, course_id, request.user, week)


@router.get("/{roadmap_id}/topics/{topic_id}", response=CoursePlayer)
def get_topic(request, roadmap_id: int, topic_id: int):
    """The player of the roadmap course containing this topic, opened on it."""
    roadmap = get_object_or_404(RoadMap, pk=roadmap_id)
    course_id = course_for_topic(roadmap, topic_id)
    return course_player(roadmap, course_id, request.user, topic_pk=topic_id)
