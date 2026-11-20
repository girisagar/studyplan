from datetime import date, datetime

from ninja import ModelSchema, Schema

from config.schemas import RichHTML
from curriculum.schemas import (
    ChapterOut,
    ChapterRef,
    CourseOut,
    CourseRef,
    TopicBrief,
    TopicOut,
)
from library.schemas import ResourceOut
from progress.schemas import EnrollmentOut, ProgressOut
from .models import RoadMap


class RoadMapRef(ModelSchema):
    class Meta:
        model = RoadMap
        fields = ["id", "name"]


class RoadMapOut(RoadMapRef):
    description: RichHTML
    note_count: int = 0


# Outline ------------------------------------------------------------------
# Weeks are on the roadmap timeline (course start_week + chapter week - 1).


class OutlineTopic(TopicBrief):
    note_count: int = 0


class OutlineChapter(ChapterRef):
    note_count: int = 0
    position: int | None = None  # 1-based number of the chapter in its course


class OutlineItem(Schema):
    """A topic in outline order; `number` counts from 1 across the outline."""

    number: int
    week: int
    completed: bool
    course: CourseRef
    chapter: OutlineChapter
    topic: OutlineTopic


class OutlineGroup(Schema):
    """One chapter's topics within a week."""

    course: CourseRef
    chapter: OutlineChapter
    items: list[OutlineItem]
    completed: int
    hours: int
    percent: int


class OutlineSection(Schema):
    """A roadmap week; parallel courses each contribute a group."""

    week: int
    title: str
    total: int
    completed: int
    hours: int
    percent: int
    courses: list[CourseRef]
    groups: list[OutlineGroup]


# Schedule -----------------------------------------------------------------


class ScheduledCourseBrief(Schema):
    """A course placed on the roadmap, with its range on the roadmap timeline.
    `progress` is set for signed-in users; `state` is done/current/upcoming."""

    course: CourseRef
    start_week: int
    order: int
    first_week: int
    last_week: int
    weeks: int
    topic_count: int
    hours: int
    progress: ProgressOut | None = None
    state: str | None = None


class ScheduledCourseOut(ScheduledCourseBrief):
    course: CourseOut


class RoadMapListItem(RoadMapOut):
    topic_count: int
    hours: int
    weeks: int
    following: bool
    progress: ProgressOut | None
    next_item: OutlineItem | None
    schedule: list[ScheduledCourseBrief]


class RoadMapDetail(RoadMapOut):
    """The roadmap overview. `finish` is todo/progress/complete; `progress` and
    `enrollment` are set only when the user follows the roadmap."""

    enrollment: EnrollmentOut | None
    progress: ProgressOut | None
    schedule: list[ScheduledCourseOut]
    sections: list[OutlineSection]
    next_item: OutlineItem | None
    resources: list[ResourceOut]
    finish: str
    total_weeks: int
    total_topics: int
    total_hours: int


# Course player ------------------------------------------------------------


class PlayerItem(Schema):
    """The topic being studied, with full chapter and topic content."""

    number: int
    week: int
    completed: bool
    course: CourseRef
    chapter: ChapterOut
    topic: TopicOut


class TopicPanel(Schema):
    """The player's content pane: the current topic and its neighbours in the
    course (null at either end)."""

    roadmap: RoadMapRef
    course: CourseRef
    enrollment: EnrollmentOut | None
    current: PlayerItem | None
    previous: OutlineItem | None
    next: OutlineItem | None
    total_items: int


class CoursePlayer(TopicPanel):
    """A course of a roadmap: the topic pane plus the course's week outline."""

    course: CourseOut
    placement: ScheduledCourseBrief
    progress: ProgressOut | None
    sections: list[OutlineSection]


# Dashboard and progress overview -------------------------------------------


class SnapshotOut(Schema):
    """Where the user stands in a followed roadmap. `scheduled_week` is the week
    the schedule expects by now (from started_at); `pace` is
    ahead/on_track/behind/done."""

    roadmap: RoadMapRef
    enrollment: EnrollmentOut | None
    progress: ProgressOut | None
    schedule: list[ScheduledCourseBrief]
    next: OutlineItem | None
    current_section: OutlineSection | None
    weeks: int
    scheduled_week: int | None
    pace: str | None
    hours_total: int
    hours_done: int


class StudyStats(Schema):
    """`hours_done` is the estimated hours of completed topics."""

    completed: int
    this_week: int
    hours_done: int


class DashboardStats(StudyStats):
    following: int


class DashboardOut(Schema):
    """Home: the most recently active roadmap, the others, materials for the
    next topic, stats; `roadmaps` lists all roadmaps when none are followed."""

    active: SnapshotOut | None
    others: list[SnapshotOut]
    materials: list[ResourceOut]
    stats: DashboardStats
    roadmaps: list[RoadMapOut]


class RecentCompletion(Schema):
    topic: TopicBrief
    course: CourseRef
    completed_at: datetime
    roadmap_id: int | None


class WeekCount(Schema):
    """Completions in the week starting on Monday `start`; `height` is the
    percentage of the busiest of the weeks returned."""

    start: date
    count: int
    height: int


class ProgressOverview(Schema):
    snapshots: list[SnapshotOut]
    recent: list[RecentCompletion]
    weeks: list[WeekCount]
    stats: StudyStats
