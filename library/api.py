from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404
from ninja import Router

from accounts.auth import optional_auth
from notes.services import attach_note_counts
from .models import Resource
from .schemas import KindOut, ResourceDetail, ResourceListItem
from .services import chapters_with_placements, roadmap_links, topics_with_placements

router = Router(tags=["library"], auth=optional_auth)


@router.get("/resources", response=list[ResourceListItem])
def list_resources(request, kind: str = "", q: str = ""):
    """Every resource, optionally filtered by `kind` and searched (`q`) by
    title/author, with the roadmaps that use it."""
    resources = Resource.objects.prefetch_related(
        "courses__roadmap_links__roadmap",
        "chapters__course__roadmap_links__roadmap",
        "topics__chapter__course__roadmap_links__roadmap",
    )
    if kind:
        resources = resources.filter(kind=kind)
    if q.strip():
        resources = resources.filter(
            Q(title__icontains=q.strip()) | Q(author__icontains=q.strip())
        )
    resources = list(resources)
    for resource in resources:
        resource.roadmaps = list(
            dict.fromkeys(link.roadmap for link in roadmap_links(resource))
        )
    return resources


@router.get("/kinds", response=list[KindOut])
def list_kinds(request):
    """The resource kinds in use, in display order (for the kind filter)."""
    used = set(Resource.objects.values_list("kind", flat=True).distinct())
    return [
        {"value": value, "label": label}
        for value, label in Resource.Kind.choices
        if value in used
    ]


@router.get("/resources/{resource_id}", response=ResourceDetail)
def get_resource(request, resource_id: int):
    """A resource and everywhere it is used, with weeks on each roadmap's timeline."""
    resource = get_object_or_404(
        Resource.objects.prefetch_related(
            "courses__roadmap_links__roadmap",
            Prefetch("chapters", queryset=chapters_with_placements()),
            Prefetch("topics", queryset=topics_with_placements()),
        ),
        pk=resource_id,
    )
    attach_note_counts([resource], request.user)
    chapters = [
        {
            "id": chapter.pk,
            "name": chapter.name,
            "course": chapter.course,
            "roadmap": link.roadmap,
            "week": link.start_week + chapter.week - 1,
        }
        for chapter in resource.chapters.all()
        for link in chapter.course.roadmap_links.all()
    ]
    topics = [
        {
            "id": topic.pk,
            "topic_name": topic.topic_name,
            "chapter": topic.chapter,
            "course": topic.chapter.course,
            "roadmap": link.roadmap,
            "week": link.start_week + topic.chapter.week - 1,
        }
        for topic in resource.topics.all()
        for link in topic.chapter.course.roadmap_links.all()
    ]
    return {
        "resource": resource,
        "note_count": resource.note_count,
        "placements": roadmap_links(resource),
        "courses": list(resource.courses.all()),
        "chapters": chapters,
        "topics": topics,
    }
