from django.contrib import admin
from django.utils.html import format_html

from .models import Resource


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ["title", "kind", "author", "preview"]
    list_filter = ["kind"]
    search_fields = ["title", "author", "url"]
    readonly_fields = ["preview"]
    fields = ["title", "author", "kind", "file", "url", "thumbnail", "preview"]

    @admin.display(description="Thumbnail")
    def preview(self, obj):
        if not obj or not obj.thumbnail:
            return "No thumbnail"
        return format_html(
            '<img src="{}" alt="{} thumbnail" style="max-height: 180px; max-width: 120px;">',
            obj.thumbnail.url,
            obj.title,
        )
