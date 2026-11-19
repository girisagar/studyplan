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


class CompletionIn(Schema):
    completed: bool


class CompletionOut(Schema):
    completed: bool
    progress: ProgressOut
    course: ProgressOut
