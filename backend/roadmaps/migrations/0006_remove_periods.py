from django.db import migrations


def delete_old_structure(apps, schema_editor):
    """Old per-book roadmaps (no courses) with their periods and enrollments."""
    RoadMap = apps.get_model("roadmaps", "RoadMap")
    UserRoadMap = apps.get_model("progress", "UserRoadMap")
    old = RoadMap.objects.filter(course_links__isnull=True)
    UserRoadMap.objects.filter(roadmap__in=old).delete()
    apps.get_model("roadmaps", "PeriodChapter").objects.all().delete()
    apps.get_model("roadmaps", "RoadMapPeriod").objects.all().delete()
    old.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("progress", "0004_progress_per_user_topic"),
        ("roadmaps", "0005_courses_from_roadmaps"),
    ]

    operations = [
        migrations.RunPython(delete_old_structure, migrations.RunPython.noop),
        migrations.DeleteModel(name="PeriodChapter"),
        migrations.DeleteModel(name="RoadMapPeriod"),
        migrations.RemoveField(model_name="roadmap", name="duration"),
        migrations.RemoveField(model_name="roadmap", name="unit"),
        migrations.RemoveField(model_name="roadmap", name="books"),
    ]
