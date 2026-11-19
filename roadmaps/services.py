"""Derived roadmap data served by the REST API.

Nothing here is stored: schedules, week outlines, snapshots and stats are all
computed from chapters, topics, enrollments and completions.
"""

from datetime import datetime, time, timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncWeek
from django.http import Http404
from django.utils import timezone

from notes.services import attach_note_counts
from progress.models import (
    UserRoadMap,
    UserTopicProgress,
    course_progress,
    roadmap_progress,
)
from .models import RoadMap


def course_schedule(roadmap):
    """The roadmap's course links in timeline order, each annotated with
    `first_week`/`last_week` on the roadmap timeline, `topic_count` and `hours`
    (chapters and topics prefetched)."""
    links = list(
        roadmap.course_links.select_related("course").prefetch_related(
            "course__resources",
            "course__chapters__resources",
            "course__chapters__topics__tags",
            "course__chapters__topics__resources",
        )
    )
    for link in links:
        chapters = link.course.chapters.all()
        weeks = [c.week for c in chapters] or [1]
        link.first_week = link.start_week + min(weeks) - 1
        link.last_week = link.start_week + max(weeks) - 1
        link.weeks = link.last_week - link.first_week + 1
        topics = [t for c in chapters for t in c.topics.all()]
        link.topic_count = len(topics)
        link.hours = sum(t.total_time for t in topics)
    return links


def build_outline(schedule, done):
    """Week-by-week outline of the given course links.

    Returns (sections, items). `sections` has one entry per roadmap week that has
    chapters; within a week, chapters of different courses (parallel courses) are
    ordered by course order, then chapter order. `items` is the flat topic list in
    that order, numbered from 1; `done` is the set of completed topic ids.
    Sections and their chapter groups carry completed/hours/percent totals.
    """
    by_week = {}
    for position, link in enumerate(schedule):
        for chapter in link.course.chapters.all():
            week = link.start_week + chapter.week - 1
            sort_key = (link.order, position, chapter.order, chapter.pk)
            by_week.setdefault(week, []).append((sort_key, link.course, chapter))
    sections, items = [], []
    for week in sorted(by_week):
        section = {"week": week, "groups": [], "total": 0, "completed": 0, "hours": 0}
        for _, course, chapter in sorted(by_week[week], key=lambda e: e[0]):
            rows = []
            for topic in chapter.topics.all():
                item = {
                    "number": len(items) + 1,
                    "key": str(topic.pk),
                    "week": week,
                    "course": course,
                    "chapter": chapter,
                    "topic": topic,
                    "completed": topic.pk in done,
                }
                items.append(item)
                rows.append(item)
                section["total"] += 1
                section["completed"] += item["completed"]
                section["hours"] += topic.total_time
            completed = sum(i["completed"] for i in rows)
            section["groups"].append(
                {
                    "course": course,
                    "chapter": chapter,
                    "items": rows,
                    "completed": completed,
                    "hours": sum(i["topic"].total_time for i in rows),
                    "percent": round(100 * completed / len(rows)) if rows else 0,
                }
            )
        section["percent"] = (
            round(100 * section["completed"] / section["total"])
            if section["total"]
            else 0
        )
        section["title"] = " · ".join(g["chapter"].name for g in section["groups"])
        section["courses"] = list(dict.fromkeys(g["course"] for g in section["groups"]))
        sections.append(section)
    return sections, items


def pick_item(sections, items, week, topic_pk):
    """The item to show: the requested topic, else the first unfinished one
    (in the requested week, or the whole outline), else the first one."""
    if topic_pk is not None:
        item = next((i for i in items if i["topic"].pk == topic_pk), None)
        if item is None:
            raise Http404
        return item
    if week is not None and not any(s["week"] == week for s in sections):
        raise Http404
    pool = [i for i in items if week is None or i["week"] == week]
    return next((i for i in pool if not i["completed"]), pool[0] if pool else None)


def completed_topic_ids(user):
    if not user.is_authenticated:
        return set()
    return set(
        UserTopicProgress.objects.filter(user=user).values_list("topic_id", flat=True)
    )


def roadmap_snapshot(roadmap, done, enrollment=None, progress=None):
    """Where a learner stands in a roadmap: next topic, current week, hours, pace.

    `progress` is the roadmap's entry from roadmap_progress() (the single source
    of completed/total/percent); it is None for roadmaps the user doesn't follow.
    """
    schedule = course_schedule(roadmap)
    sections, items = build_outline(schedule, done)
    next_item = next((i for i in items if not i["completed"]), None)
    weeks = max((link.last_week for link in schedule), default=0)
    current_section = None
    if next_item:
        current_section = next(s for s in sections if s["week"] == next_item["week"])
    scheduled_week = pace = None
    if enrollment and weeks:
        elapsed = (
            timezone.localdate() - timezone.localdate(enrollment.started_at)
        ).days
        scheduled_week = min(weeks, max(1, elapsed // 7 + 1))
        if next_item is None:
            pace = "done"
        elif next_item["week"] > scheduled_week:
            pace = "ahead"
        elif next_item["week"] < scheduled_week:
            pace = "behind"
        else:
            pace = "on_track"
    return {
        "roadmap": roadmap,
        "enrollment": enrollment,
        "progress": progress,
        "schedule": schedule,
        "sections": sections,
        "items": items,
        "next": next_item,
        "current_section": current_section,
        "weeks": weeks,
        "scheduled_week": scheduled_week,
        "pace": pace,
        "hours_total": sum(i["topic"].total_time for i in items),
        "hours_done": sum(i["topic"].total_time for i in items if i["completed"]),
    }


def enrollment_snapshots(user):
    """Snapshots of the roadmaps the user follows, most recently active first."""
    enrollments = list(UserRoadMap.objects.filter(user=user).select_related("roadmap"))
    if not enrollments:
        return []
    done = completed_topic_ids(user)
    progress = roadmap_progress(user, [e.roadmap_id for e in enrollments])
    snapshots = [
        roadmap_snapshot(e.roadmap, done, e, progress[e.roadmap_id])
        for e in enrollments
    ]
    last_activity = {
        s["roadmap"].pk: _last_completed(user, s["roadmap"]) for s in snapshots
    }
    snapshots.sort(
        key=lambda s: (
            last_activity[s["roadmap"].pk] or s["enrollment"].started_at,
            s["enrollment"].started_at,
        ),
        reverse=True,
    )
    return snapshots


def _last_completed(user, roadmap):
    return (
        UserTopicProgress.objects.filter(
            user=user, topic__chapter__course__roadmap_links__roadmap=roadmap
        )
        .order_by("-completed_at")
        .values_list("completed_at", flat=True)
        .first()
    )


def study_stats(user):
    """Completed topics, completed this week and their estimated hours (each
    topic counted once, even if it appears in several roadmaps)."""
    completions = UserTopicProgress.objects.filter(user=user)
    return {
        "completed": completions.count(),
        "this_week": completions.filter(completed_at__gte=week_start()).count(),
        "hours_done": completions.aggregate(h=Sum("topic__total_time"))["h"] or 0,
    }


def week_start():
    """Start (Monday 00:00, local time) of the current week."""
    today = timezone.localdate()
    monday = today - timedelta(days=today.weekday())
    return timezone.make_aware(datetime.combine(monday, time.min))


def weekly_completions(user, weeks=8):
    """Completions per week (Monday start) for the last `weeks` weeks, oldest
    first, each with `height` as a percentage of the busiest week."""
    start = week_start() - timedelta(weeks=weeks - 1)
    counts = {
        timezone.localdate(row["week"]): row["n"]
        for row in UserTopicProgress.objects.filter(user=user, completed_at__gte=start)
        .annotate(week=TruncWeek("completed_at"))
        .values("week")
        .annotate(n=Count("pk"))
    }
    result = []
    for offset in range(weeks):
        monday = timezone.localdate(start) + timedelta(weeks=offset)
        result.append({"start": monday, "count": counts.get(monday, 0)})
    peak = max((w["count"] for w in result), default=0) or 1
    for w in result:
        w["height"] = round(100 * w["count"] / peak)
    return result


def recent_completions(user, followed_roadmap_ids, limit=12):
    """The user's latest completions, each with `roadmap_id` set to a followed
    roadmap that contains the topic (or None)."""
    recent = list(
        UserTopicProgress.objects.filter(user=user)
        .select_related("topic__chapter__course")
        .prefetch_related("topic__chapter__course__roadmap_links")
        .order_by("-completed_at")[:limit]
    )
    for row in recent:
        row.roadmap_id = next(
            (
                link.roadmap_id
                for link in row.topic.chapter.course.roadmap_links.all()
                if link.roadmap_id in followed_roadmap_ids
            ),
            None,
        )
    return recent


def dashboard_materials(snapshot, limit=6):
    """Distinct resources of the snapshot's next topic, its chapter and course."""
    if not snapshot or not snapshot["next"]:
        return []
    current = snapshot["next"]
    groups = [
        current["topic"].resources.all(),
        current["chapter"].resources.all(),
        current["course"].resources.all(),
    ]
    return list(dict.fromkeys(r for group in groups for r in group))[:limit]


def get_enrollment(user, roadmap):
    if not user.is_authenticated:
        return None
    return UserRoadMap.objects.filter(user=user, roadmap=roadmap).first()


def roadmap_cards(user):
    """Every roadmap with topic/hour/week totals, its course schedule and, for
    roadmaps the user follows, progress and the next unfinished topic."""
    roadmaps = list(
        RoadMap.objects.annotate(
            topic_count=Count("course_links__course__chapters__topics"),
            hours=Sum("course_links__course__chapters__topics__total_time"),
        )
    )
    followed, progress = set(), {}
    done = completed_topic_ids(user)
    if user.is_authenticated:
        followed = set(
            UserRoadMap.objects.filter(user=user).values_list("roadmap_id", flat=True)
        )
        progress = roadmap_progress(user, followed)
    for roadmap in roadmaps:
        roadmap.hours = roadmap.hours or 0
        roadmap.schedule = course_schedule(roadmap)
        roadmap.weeks = max((l.last_week for l in roadmap.schedule), default=0)
        roadmap.following = roadmap.pk in followed
        roadmap.progress = progress.get(roadmap.pk)
        roadmap.next_item = None
        if roadmap.following:
            _, items = build_outline(roadmap.schedule, done)
            roadmap.next_item = next((i for i in items if not i["completed"]), None)
    attach_note_counts(roadmaps, user)
    return roadmaps


def roadmap_overview(roadmap, user):
    """Everything the roadmap overview shows: course schedule with per-course
    progress and timeline state, the week-by-week outline, next topic, totals."""
    enrollment = get_enrollment(user, roadmap)
    schedule = course_schedule(roadmap)
    # Timeline state: "done", "current" (first unfinished course) or "upcoming".
    for link in schedule:
        link.state = "upcoming"
        link.progress = None
    if user.is_authenticated:
        per_course = course_progress(user, [l.course_id for l in schedule])
        for link in schedule:
            link.progress = per_course[link.course_id]
            p = link.progress
            if p["total"] and p["completed"] == p["total"]:
                link.state = "done"
        current = next((l for l in schedule if l.state != "done"), None)
        if current:
            current.state = "current"
    # Overall status shown at the end of the timeline.
    completed = sum(l.progress["completed"] for l in schedule if l.progress)
    total = sum(l.topic_count for l in schedule)
    if total and completed == total:
        finish = "complete"
    elif completed:
        finish = "progress"
    else:
        finish = "todo"
    attach_note_counts([roadmap, *(l.course for l in schedule)], user)
    # Week-by-week outline of the whole roadmap, with each chapter numbered
    # within its course and its own completion/hours.
    for link in schedule:
        for position, chapter in enumerate(link.course.chapters.all(), start=1):
            chapter.position = position
    sections, items = build_outline(schedule, completed_topic_ids(user))
    return {
        "roadmap": roadmap,
        "enrollment": enrollment,
        "schedule": schedule,
        "sections": sections,
        "next_item": next((i for i in items if not i["completed"]), None),
        "resources": list(
            dict.fromkeys(r for link in schedule for r in link.course.resources.all())
        ),
        "finish": finish,
        "total_weeks": max((l.last_week for l in schedule), default=0),
        "total_topics": total,
        "total_hours": sum(l.hours for l in schedule),
        "progress": (
            roadmap_progress(user, [roadmap.pk])[roadmap.pk] if enrollment else None
        ),
    }


def course_player(roadmap, course_pk, user, week=None, topic_pk=None):
    """The course player for a course of the roadmap: the current topic (the
    requested one, else the first unfinished one in `week` or the course), its
    neighbours, and the course's week outline. Http404 if the course isn't on
    the roadmap or the week/topic isn't in the course."""
    link = next((l for l in course_schedule(roadmap) if l.course_id == course_pk), None)
    if link is None:
        raise Http404
    course = link.course
    done = set()
    if user.is_authenticated:
        done = set(
            UserTopicProgress.objects.filter(
                user=user, topic__chapter__course=course
            ).values_list("topic_id", flat=True)
        )
    sections, items = build_outline([link], done)
    note_targets = [course]
    note_targets.extend(g["chapter"] for s in sections for g in s["groups"])
    note_targets.extend(item["topic"] for item in items)
    attach_note_counts(note_targets, user)
    current = pick_item(sections, items, week, topic_pk)
    previous = following = None
    if current:
        index = current["number"] - 1
        previous = items[index - 1] if index > 0 else None
        following = items[index + 1] if index + 1 < len(items) else None
    enrollment = get_enrollment(user, roadmap)
    return {
        "roadmap": roadmap,
        "course": course,
        "link": link,
        "placement": link,
        "enrollment": enrollment,
        "current": current,
        "previous": previous,
        "next": following,
        "total_items": len(items),
        "sections": sections,
        "resources": list(course.resources.all()),
        "progress": (
            course_progress(user, [course.pk])[course.pk] if enrollment else None
        ),
    }


def course_for_week(roadmap, week):
    """The id of the first course (in timeline order) with a chapter in `week`."""
    for link in course_schedule(roadmap):
        if any(
            link.start_week + c.week - 1 == week for c in link.course.chapters.all()
        ):
            return link.course_id
    raise Http404


def course_for_topic(roadmap, topic_pk):
    """The id of the roadmap course that contains the topic."""
    link = roadmap.course_links.filter(course__chapters__topics=topic_pk).first()
    if link is None:
        raise Http404
    return link.course_id
