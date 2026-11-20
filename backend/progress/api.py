"""The signed-in user's enrollments, topic completion, dashboard and progress
overview. All progress numbers come from roadmap_progress()/course_progress()."""

from django.shortcuts import get_object_or_404
from ninja import Router

from roadmaps.models import RoadMap
from roadmaps.schemas import DashboardOut, ProgressOverview
from roadmaps.services import (
    dashboard_materials,
    enrollment_snapshots,
    recent_completions,
    study_stats,
    weekly_completions,
)
from .models import UserRoadMap, UserTopicProgress, course_progress, roadmap_progress
from .schemas import (
    CompletionIn,
    CompletionOut,
    CompletionRecordOut,
    EnrollmentIn,
    EnrollmentOut,
    RoadMapProgressOut,
)
from .services import not_future, set_completion

router = Router(tags=["progress"])


@router.get("/enrollments", response=list[EnrollmentOut])
def list_enrollments(request):
    """Roadmaps the user follows, most recently started first."""
    return (
        UserRoadMap.objects.filter(user=request.user)
        .select_related("roadmap")
        .order_by("-started_at")
    )


@router.put("/roadmaps/{roadmap_id}/enrollment", response=EnrollmentOut)
def enroll(request, roadmap_id: int, payload: EnrollmentIn | None = None):
    """Follow a roadmap. Idempotent: following again keeps the original start."""
    roadmap = get_object_or_404(RoadMap, pk=roadmap_id)
    started_at = not_future(payload.started_at if payload else None)
    enrollment, _ = UserRoadMap.objects.get_or_create(
        user=request.user, roadmap=roadmap, defaults={"started_at": started_at}
    )
    return enrollment


@router.get("/completions", response=list[CompletionRecordOut])
def list_completions(request):
    """Every topic the user has completed (shared by all roadmaps containing
    it), for clients that keep progress offline."""
    return UserTopicProgress.objects.filter(user=request.user).order_by("completed_at")


@router.get("/roadmaps", response=list[RoadMapProgressOut])
def list_roadmap_progress(request):
    """Completed/total topics for each roadmap the user follows."""
    ids = UserRoadMap.objects.filter(user=request.user).values_list(
        "roadmap_id", flat=True
    )
    progress = roadmap_progress(request.user, ids)
    return [{"roadmap_id": rid, **p} for rid, p in progress.items()]


@router.put(
    "/roadmaps/{roadmap_id}/topics/{topic_id}/completion", response=CompletionOut
)
def set_topic_completion(
    request, roadmap_id: int, topic_id: int, payload: CompletionIn
):
    """Set (not toggle) a topic's completion. 404 unless the user follows the
    roadmap and the topic is part of it. Returns the roadmap's progress and the
    topic's course progress."""
    return set_completion(
        request.user, roadmap_id, topic_id, payload.completed, payload.completed_at
    )


@router.get("/dashboard", response=DashboardOut)
def dashboard(request):
    """Home: continue learning (most recently active roadmap first), materials
    for the next topic, stats; all roadmaps when the user follows none."""
    user = request.user
    snapshots = enrollment_snapshots(user)
    active = snapshots[0] if snapshots else None
    return {
        "active": active,
        "others": snapshots[1:],
        "materials": dashboard_materials(active),
        "stats": {**study_stats(user), "following": len(snapshots)},
        "roadmaps": [] if snapshots else RoadMap.objects.all(),
    }


@router.get("/overview", response=ProgressOverview)
def overview(request):
    """Per-roadmap and per-course progress, pace, recent activity and
    completions per week for the last 8 weeks."""
    user = request.user
    snapshots = enrollment_snapshots(user)
    course_ids = [link.course_id for s in snapshots for link in s["schedule"]]
    per_course = course_progress(user, course_ids)
    for snap in snapshots:
        for link in snap["schedule"]:
            link.progress = per_course[link.course_id]
    recent = recent_completions(user, {s["roadmap"].pk for s in snapshots})
    for row in recent:
        row.course = row.topic.chapter.course
    return {
        "snapshots": snapshots,
        "recent": recent,
        "weeks": weekly_completions(user),
        "stats": study_stats(user),
    }
