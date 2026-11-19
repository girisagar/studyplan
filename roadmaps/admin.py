from django.contrib import admin
from .models import RoadMap, RoadMapCourse


class RoadMapCourseInline(admin.TabularInline):
    model = RoadMapCourse
    extra = 0
    autocomplete_fields = ["course"]


@admin.register(RoadMap)
class RoadMapAdmin(admin.ModelAdmin):
    list_display = ["name"]
    inlines = [RoadMapCourseInline]
