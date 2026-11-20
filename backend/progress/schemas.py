from datetime import datetime

from ninja import Field, Schema


class ProgressOut(Schema):
    """Completed/total topics; always from roadmap_progress()/course_progress()."""

    completed: int
    total: int
    percent: int


class EnrollmentOut(Schema):
    """The user follows this roadmap since `started_at`."""

    roadmap_id: int
    roadmap_name: str = Field(..., alias="roadmap.name")
    started_at: datetime


class RoadMapProgressOut(ProgressOut):
    roadmap_id: int


class EnrollmentIn(Schema):
    """`started_at`: when the user started following (e.g. recorded offline);
    defaults to now, never in the future."""

    started_at: datetime | None = None


class CompletionIn(Schema):
    """`completed_at`: when the topic was completed (e.g. recorded offline and
    synced later); defaults to now, never in the future. Ignored if the topic is
    already completed (its original time is kept)."""

    completed: bool
    completed_at: datetime | None = None


class CompletionRecordOut(Schema):
    topic_id: int
    completed_at: datetime


class CompletionOut(Schema):
    completed: bool
    progress: ProgressOut
    course: ProgressOut
