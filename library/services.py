"""Where library resources are used in the curriculum (used by the API)."""

from curriculum.models import Chapter, Topic


def roadmap_links(resource):
    """Distinct (roadmap, course) placements of the courses that use this resource,
    directly or through one of their chapters/topics."""
    seen, links = set(), []
    courses = list(resource.courses.all())
    courses += [chapter.course for chapter in resource.chapters.all()]
    courses += [topic.chapter.course for topic in resource.topics.all()]
    for course in courses:
        for link in course.roadmap_links.all():
            if link.pk not in seen:
                seen.add(link.pk)
                links.append(link)
    return links


def chapters_with_placements():
    return Chapter.objects.select_related("course").prefetch_related(
        "course__roadmap_links__roadmap"
    )


def topics_with_placements():
    return Topic.objects.select_related("chapter__course").prefetch_related(
        "chapter__course__roadmap_links__roadmap"
    )
