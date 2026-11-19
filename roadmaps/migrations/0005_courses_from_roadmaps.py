"""Turn each old roadmap into a course, and gather the courses into one roadmap.

Before: RoadMap (one per book) -> RoadMapPeriod (week) -> PeriodChapter -> Chapter.
After:  RoadMap -> RoadMapCourse(start_week) -> Course -> Chapter(week, order, deliverable).

Chapter and topic primary keys are kept, so notes on chapters/topics survive.
Progress is re-keyed from (enrollment, assignment, topic) to (user, topic).
"""

from django.db import migrations

NEW_ROADMAP_NAME = "ML Quant Research Path"


def split_deliverable(text, parts):
    """One deliverable per chapter: split a shared week deliverable on ';'."""
    if parts == 1:
        return [text]
    pieces = [p.strip() for p in text.split(";") if p.strip()]
    if len(pieces) != parts:
        return [text] + [""] * (parts - 1)
    return [p[0].upper() + p[1:] + ("" if p.endswith(".") else ".") for p in pieces]


def forwards(apps, schema_editor):
    RoadMap = apps.get_model("roadmaps", "RoadMap")
    RoadMapCourse = apps.get_model("roadmaps", "RoadMapCourse")
    Course = apps.get_model("curriculum", "Course")
    Chapter = apps.get_model("curriculum", "Chapter")
    UserRoadMap = apps.get_model("progress", "UserRoadMap")
    UserTopicProgress = apps.get_model("progress", "UserTopicProgress")
    Note = apps.get_model("notes", "Note")
    ContentType = apps.get_model("contenttypes", "ContentType")

    old_roadmaps = list(
        RoadMap.objects.filter(course_links__isnull=True).order_by("pk")
    )
    if not old_roadmaps:
        return
    new_roadmap = RoadMap.objects.create(
        name=NEW_ROADMAP_NAME,
        description="<p>The full path, one course after another.</p>",
        duration=1,  # legacy column, dropped in 0006
        unit="week",
    )

    course_for = {}
    start_week = 1
    for order, old in enumerate(old_roadmaps, 1):
        course = Course.objects.create(name=old.name, description=old.description)
        course.books.set(old.books.all())
        course_for[old.pk] = course
        weeks = 0
        for period in old.periods.order_by("sequence"):
            assignments = list(period.period_chapters.order_by("order", "pk"))
            deliverables = split_deliverable(period.deliverable, len(assignments))
            for position, (pc, deliverable) in enumerate(
                zip(assignments, deliverables), 1
            ):
                Chapter.objects.filter(pk=pc.chapter_id).update(
                    course=course,
                    week=period.sequence,
                    order=position,
                    deliverable=deliverable,
                )
            weeks = max(weeks, period.sequence)
        RoadMapCourse.objects.create(
            roadmap=new_roadmap, course=course, order=order, start_week=start_week
        )
        start_week += max(weeks, 1)

    # Chapters that were never scheduled still need a course.
    orphans = Chapter.objects.filter(course__isnull=True)
    if orphans.exists():
        unscheduled = Course.objects.create(name="Unscheduled chapters")
        orphans.update(course=unscheduled)

    # Progress: (user, topic), completed rows only, one row per pair.
    UserTopicProgress.objects.filter(completed=False).delete()
    seen = set()
    for row in UserTopicProgress.objects.select_related("enrollment").order_by(
        "completed_at", "pk"
    ):
        key = (row.enrollment.user_id, row.topic_id)
        if key in seen:
            row.delete()
            continue
        seen.add(key)
        row.user_id = key[0]
        row.completed_at = row.completed_at or row.enrollment.started_at
        row.save(update_fields=["user", "completed_at"])

    # Enrollments: one per user on the new roadmap, keeping the earliest start.
    first_start = {}
    for enrollment in UserRoadMap.objects.order_by("started_at"):
        first_start.setdefault(enrollment.user_id, enrollment.started_at)
    for user_id, started_at in first_start.items():
        UserRoadMap.objects.create(
            user_id=user_id, roadmap=new_roadmap, started_at=started_at
        )

    # Notes written on an old roadmap now belong to the course it became.
    roadmap_ct = ContentType.objects.filter(app_label="roadmaps", model="roadmap")
    if roadmap_ct.exists():
        course_ct, _ = ContentType.objects.get_or_create(
            app_label="curriculum", model="course"
        )
        for note in Note.objects.filter(content_type=roadmap_ct.get()):
            if note.object_id in course_for:
                note.content_type = course_ct
                note.object_id = course_for[note.object_id].pk
                note.save(update_fields=["content_type", "object_id"])

    # The old roadmaps, periods, assignments and enrollments are deleted in 0006,
    # after progress.0004 drops the progress -> enrollment/assignment columns
    # (deleting an old enrollment now would cascade to the progress rows).


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("curriculum", "0009_course"),
        ("notes", "0002_alter_note_body"),
        ("progress", "0003_usertopicprogress_user"),
        ("roadmaps", "0004_roadmapcourse"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
