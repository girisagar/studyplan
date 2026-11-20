import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("curriculum", "0009_course"),
        ("roadmaps", "0003_roadmap_description_richtext"),
    ]

    operations = [
        migrations.CreateModel(
            name="RoadMapCourse",
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
                (
                    "order",
                    models.PositiveIntegerField(
                        default=0, help_text="Order among courses that share a week"
                    ),
                ),
                (
                    "start_week",
                    models.PositiveSmallIntegerField(
                        default=1,
                        validators=[django.core.validators.MinValueValidator(1)],
                    ),
                ),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="roadmap_links",
                        to="curriculum.course",
                    ),
                ),
                (
                    "roadmap",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="course_links",
                        to="roadmaps.roadmap",
                    ),
                ),
            ],
            options={
                "ordering": ["start_week", "order", "pk"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("roadmap", "course"), name="unique_roadmap_course"
                    )
                ],
            },
        ),
        migrations.AddField(
            model_name="roadmap",
            name="courses",
            field=models.ManyToManyField(
                related_name="roadmaps",
                through="roadmaps.RoadMapCourse",
                to="curriculum.course",
            ),
        ),
    ]
