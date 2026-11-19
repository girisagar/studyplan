from ninja import ModelSchema, Schema

from config.schemas import absolute_url
from .models import Resource


class ResourceOut(ModelSchema):
    """A study resource. `href` is where to open it: the uploaded file if any,
    else its URL. File and thumbnail URLs are absolute."""

    kind_label: str
    href: str | None
    file_url: str | None
    thumbnail_url: str | None
    is_pdf: bool

    class Meta:
        model = Resource
        fields = ["id", "title", "author", "kind", "url"]

    @staticmethod
    def resolve_kind_label(obj):
        return obj.get_kind_display()

    @staticmethod
    def resolve_file_url(obj, context):
        return absolute_url(context, obj.file.url if obj.file else None)

    @staticmethod
    def resolve_thumbnail_url(obj, context):
        return absolute_url(context, obj.thumbnail.url if obj.thumbnail else None)

    @staticmethod
    def resolve_href(obj, context):
        return absolute_url(context, obj.href)


class KindOut(Schema):
    value: str
    label: str


class NamedRef(Schema):
    id: int
    name: str


class PlacementOut(Schema):
    """A course's place on a roadmap (where a resource is used)."""

    roadmap: NamedRef
    course: NamedRef
    start_week: int


class ResourceListItem(ResourceOut):
    roadmaps: list[NamedRef]


class ResourceChapterUse(Schema):
    id: int
    name: str
    course: NamedRef
    roadmap: NamedRef
    week: int


class ResourceTopicUse(Schema):
    id: int
    topic_name: str
    chapter: NamedRef
    course: NamedRef
    roadmap: NamedRef
    week: int


class ResourceDetail(Schema):
    resource: ResourceOut
    note_count: int
    placements: list[PlacementOut]
    courses: list[NamedRef]
    chapters: list[ResourceChapterUse]
    topics: list[ResourceTopicUse]
