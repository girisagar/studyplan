from django.db import migrations, models

# Old free-text `type` values (only "book" was a valid choice) -> new kinds.
KIND_FOR_TYPE = {"book": "book", "textbook": "book", "workbook": "problem_set"}


def map_kinds(apps, schema_editor):
    Resource = apps.get_model("library", "Resource")
    for resource in Resource.objects.all():
        kind = KIND_FOR_TYPE.get(resource.kind, "other")
        if kind != resource.kind:
            resource.kind = kind
            resource.save(update_fields=["kind"])


class Migration(migrations.Migration):
    """Book -> Resource: any uploaded file and/or URL, with a kind.

    Renames in place, so ids, uploaded file paths and notes are kept.
    """

    # Run after every older migration that still refers to library.Book
    # (curriculum.0009 Course.books, roadmaps.0002-0006 RoadMap.books and the
    # course data migration), or a fresh database fails to resolve it.
    dependencies = [
        ("library", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("curriculum", "0010_chapter_course_required"),
        ("roadmaps", "0006_remove_periods"),
    ]

    operations = [
        migrations.RenameModel("Book", "Resource"),
        migrations.RenameField("resource", "pdf", "file"),
        migrations.RenameField("resource", "cover_image", "thumbnail"),
        migrations.RenameField("resource", "type", "kind"),
        migrations.AlterField(
            model_name="resource",
            name="file",
            field=models.FileField(blank=True, upload_to="resources/"),
        ),
        migrations.AlterField(
            model_name="resource",
            name="thumbnail",
            field=models.ImageField(
                blank=True, null=True, upload_to="resource_thumbnails/"
            ),
        ),
        migrations.AlterField(
            model_name="resource",
            name="kind",
            field=models.CharField(
                choices=[
                    ("book", "Book"),
                    ("paper", "Paper"),
                    ("problem_set", "Problem set"),
                    ("solutions", "Solutions"),
                    ("notes", "Notes"),
                    ("code", "Code"),
                    ("slides", "Slides"),
                    ("video", "Video"),
                    ("other", "Other"),
                ],
                default="book",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="resource",
            name="url",
            field=models.URLField(blank=True, max_length=2000),
        ),
        migrations.AlterModelOptions(
            name="resource", options={"ordering": ["title", "pk"]}
        ),
        migrations.RunPython(map_kinds, migrations.RunPython.noop),
    ]
