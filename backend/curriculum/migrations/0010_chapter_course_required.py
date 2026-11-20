import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("curriculum", "0009_course"),
        ("roadmaps", "0005_courses_from_roadmaps"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chapter",
            name="course",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chapters",
                to="curriculum.course",
            ),
        ),
    ]
