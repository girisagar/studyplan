from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

NOTE_TARGETS = {
    ("curriculum", "course"),
    ("curriculum", "chapter"),
    ("curriculum", "topic"),
    ("roadmaps", "roadmap"),
    ("library", "resource"),
}


class Note(models.Model):
    title = models.CharField(max_length=255, blank=True)
    body = CKEditor5Field(verbose_name="Description")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return self.title or f"Note {self.pk or ''}".strip()

    def clean(self):
        super().clean()
        if self.content_type_id:
            target = (self.content_type.app_label, self.content_type.model)
            if target not in NOTE_TARGETS:
                raise ValidationError(
                    "Notes are not supported for this type of object."
                )
            if self.object_id is not None and self.content_object is None:
                raise ValidationError("The object for this note no longer exists.")
