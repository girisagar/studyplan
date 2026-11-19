from django.contrib import admin
from .models import Chapter, Course, Tag, Topic


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ["name", "week", "order", "deliverable"]
    show_change_link = True


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    filter_horizontal = ["resources"]
    inlines = [ChapterInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 0
    exclude = ["description"]  # rich text editor is too cramped in a table row
    autocomplete_fields = ["tags", "resources"]


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ["name", "course", "week", "order"]
    list_filter = ["course"]
    search_fields = ["name"]
    filter_horizontal = ["resources"]
    inlines = [TopicInline]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["topic_name", "chapter", "tag_names", "total_time", "order"]
    list_filter = ["tags", "chapter"]
    search_fields = ["topic_name", "tags__name"]
    autocomplete_fields = ["tags", "resources"]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("tags")

    @admin.display(description="Tags")
    def tag_names(self, obj):
        return ", ".join(tag.name for tag in obj.tags.all())
