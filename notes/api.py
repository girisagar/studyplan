"""The signed-in user's notes on courses, chapters, topics, roadmaps and
resources (targets in NOTE_TARGETS). Notes are private to their author."""

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.http import Http404
from django.shortcuts import get_object_or_404
from ninja import Router

from .models import NOTE_TARGETS, Note
from .schemas import NoteIn, NoteOut, TargetNotesOut

router = Router(tags=["notes"])


def get_target(app_label, model, object_id):
    if (app_label, model) not in NOTE_TARGETS:
        raise Http404
    return get_object_or_404(apps.get_model(app_label, model), pk=object_id)


def own_notes(request):
    return Note.objects.filter(created_by=request.user).select_related("content_type")


@router.get("/{app_label}/{model}/{object_id}", response=TargetNotesOut)
def list_target_notes(request, app_label: str, model: str, object_id: int):
    """The target (e.g. `curriculum/topic/12`) and the user's notes on it,
    newest first."""
    target = get_target(app_label, model, object_id)
    notes = own_notes(request).filter(
        content_type=ContentType.objects.get_for_model(target), object_id=target.pk
    )
    return {
        "target": {
            "app_label": app_label,
            "model": model,
            "object_id": target.pk,
            "title": str(target),
            "kind": str(target._meta.verbose_name),
        },
        "notes": notes,
    }


@router.post("/{app_label}/{model}/{object_id}", response={201: NoteOut})
def create_note(request, app_label: str, model: str, object_id: int, payload: NoteIn):
    target = get_target(app_label, model, object_id)
    note = Note.objects.create(
        created_by=request.user,
        content_type=ContentType.objects.get_for_model(target),
        object_id=target.pk,
        **payload.dict(),
    )
    return 201, note


@router.get("/{note_id}", response=NoteOut)
def get_note(request, note_id: int):
    return get_object_or_404(own_notes(request), pk=note_id)


@router.put("/{note_id}", response=NoteOut)
def update_note(request, note_id: int, payload: NoteIn):
    note = get_object_or_404(own_notes(request), pk=note_id)
    for field, value in payload.dict().items():
        setattr(note, field, value)
    note.save()
    return note


@router.delete("/{note_id}", response={204: None})
def delete_note(request, note_id: int):
    get_object_or_404(own_notes(request), pk=note_id).delete()
    return 204, None
