from collections import defaultdict
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count

from .models import Note


def attach_note_counts(objects, user):
    """Attach counts in batches, including repeated instances of the same object."""
    groups = defaultdict(list)
    for obj in objects:
        obj.note_count = 0
        groups[type(obj)].append(obj)
    if not user.is_authenticated or not groups:
        return
    content_types = ContentType.objects.get_for_models(*groups)
    for model, instances in groups.items():
        counts = dict(
            Note.objects.filter(
                created_by=user,
                content_type=content_types[model],
                object_id__in={obj.pk for obj in instances},
            )
            .values("object_id")
            .annotate(total=Count("pk"))
            .values_list("object_id", "total")
        )
        for obj in instances:
            obj.note_count = counts.get(obj.pk, 0)
