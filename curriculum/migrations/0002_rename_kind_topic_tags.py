from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("curriculum", "0001_initial"),
    ]

    # Rename first so existing "study"/"build" values carry over as the first tag.
    operations = [
        migrations.RenameField(
            model_name="topic",
            old_name="kind",
            new_name="tags",
        ),
        migrations.AlterField(
            model_name="topic",
            name="tags",
            field=models.CharField(
                blank=True,
                help_text="Comma-separated, e.g. study, statistics, python",
                max_length=255,
            ),
        ),
    ]
