import django.core.validators
import django.db.models.deletion
import django_ckeditor_5.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add Course and give chapters a course, week, order and deliverable.

    Chapter.course starts nullable; roadmaps.0005 fills it and 0010 makes it required.
    """

    dependencies = [
        ("curriculum", "0008_chapter_description_richtext"),
        ("library", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Course",
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
                ("name", models.CharField(max_length=255)),
                ("description", django_ckeditor_5.fields.CKEditor5Field(blank=True)),
                (
                    "books",
                    models.ManyToManyField(
                        blank=True, related_name="courses", to="library.book"
                    ),
                ),
            ],
            options={"ordering": ["name", "pk"]},
        ),
        migrations.AddField(
            model_name="chapter",
            name="course",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chapters",
                to="curriculum.course",
            ),
        ),
        migrations.AddField(
            model_name="chapter",
            name="week",
            field=models.PositiveSmallIntegerField(
                default=1,
                help_text="Week within the course in which this chapter is studied",
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
        migrations.AddField(
            model_name="chapter",
            name="order",
            field=models.PositiveIntegerField(
                default=0, help_text="Order within the week"
            ),
        ),
        migrations.AddField(
            model_name="chapter",
            name="deliverable",
            field=models.TextField(blank=True),
        ),
        migrations.AlterModelOptions(
            name="chapter",
            options={"ordering": ["course", "week", "order", "pk"]},
        ),
        migrations.AlterField(
            model_name="topic",
            name="total_time",
            field=models.PositiveIntegerField(
                help_text="Estimated hours",
                validators=[django.core.validators.MinValueValidator(1)],
            ),
        ),
    ]
