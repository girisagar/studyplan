import django.db.models.functions.text
from django.db import migrations, models


def split_tags_text(apps, schema_editor):
    Tag = apps.get_model("curriculum", "Tag")
    Topic = apps.get_model("curriculum", "Topic")
    for topic in Topic.objects.exclude(tags_text=""):
        tags = {}  # keyed by lowercase name, so "Python" and "python" are one tag
        for name in topic.tags_text.split(","):
            name = name.strip()
            if name and name.lower() not in tags:
                tag = Tag.objects.filter(name__iexact=name).first()
                tags[name.lower()] = tag or Tag.objects.create(name=name)
        topic.tags.add(*tags.values())


def join_tags_text(apps, schema_editor):
    Topic = apps.get_model("curriculum", "Topic")
    for topic in Topic.objects.prefetch_related("tags"):
        topic.tags_text = ", ".join(tag.name for tag in topic.tags.all())
        topic.save(update_fields=["tags_text"])


class Migration(migrations.Migration):

    dependencies = [
        ("curriculum", "0002_rename_kind_topic_tags"),
    ]

    # Keep the comma-separated text aside, copy it into Tag rows, then drop it.
    operations = [
        migrations.RenameField(
            model_name="topic",
            old_name="tags",
            new_name="tags_text",
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=50)),
            ],
            options={
                "ordering": [django.db.models.functions.text.Lower("name")],
                "constraints": [
                    models.UniqueConstraint(
                        django.db.models.functions.text.Lower("name"),
                        name="unique_tag_name_ci",
                        violation_error_message="A tag with this name already exists.",
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="topic",
            name="tags",
            field=models.ManyToManyField(
                blank=True, related_name="topics", to="curriculum.tag"
            ),
        ),
        migrations.RunPython(split_tags_text, join_tags_text),
        migrations.RemoveField(
            model_name="topic",
            name="tags_text",
        ),
    ]
