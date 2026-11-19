from ninja import ModelSchema, Schema

from config.schemas import RichHTML
from library.schemas import ResourceOut
from .models import Chapter, Course, Tag, Topic


class TagOut(ModelSchema):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class CourseRef(ModelSchema):
    class Meta:
        model = Course
        fields = ["id", "name"]


class ChapterRef(ModelSchema):
    """A chapter in an outline; `week` is the week within its course."""

    class Meta:
        model = Chapter
        fields = ["id", "name", "week", "order"]


class TopicBrief(ModelSchema):
    """A topic row in an outline. `total_time` is estimated hours."""

    tags: list[TagOut]

    class Meta:
        model = Topic
        fields = ["id", "topic_name", "total_time", "order"]


class TopicOut(TopicBrief):
    description: RichHTML
    resources: list[ResourceOut]
    note_count: int = 0


class ChapterOut(ChapterRef):
    description: RichHTML
    deliverable: str
    resources: list[ResourceOut]
    note_count: int = 0


class ChapterWithTopics(ChapterOut):
    topics: list[TopicOut]


class CourseOut(CourseRef):
    description: RichHTML
    resources: list[ResourceOut]
    note_count: int = 0


class CourseDetail(CourseOut):
    chapters: list[ChapterWithTopics]


class TopicDetail(TopicOut):
    chapter: ChapterOut
    course: CourseRef


class TopicDescriptionIn(Schema):
    description: str
