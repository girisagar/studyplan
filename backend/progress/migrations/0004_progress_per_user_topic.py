import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Progress becomes (user, topic); a row exists only while the topic is done."""

    dependencies = [
        ("curriculum", "0009_course"),
        ("progress", "0003_usertopicprogress_user"),
        ("roadmaps", "0005_courses_from_roadmaps"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="usertopicprogress",
            name="unique_progress_topic_assignment",
        ),
        migrations.RemoveField(model_name="usertopicprogress", name="enrollment"),
        migrations.RemoveField(model_name="usertopicprogress", name="period_chapter"),
        migrations.RemoveField(model_name="usertopicprogress", name="completed"),
        migrations.AlterField(
            model_name="usertopicprogress",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="topic_progress",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="usertopicprogress",
            name="topic",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="progress",
                to="curriculum.topic",
            ),
        ),
        migrations.AlterField(
            model_name="usertopicprogress",
            name="completed_at",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddConstraint(
            model_name="usertopicprogress",
            constraint=models.UniqueConstraint(
                fields=("user", "topic"), name="unique_user_topic_progress"
            ),
        ),
        migrations.RemoveField(model_name="userroadmap", name="completed_at"),
    ]
