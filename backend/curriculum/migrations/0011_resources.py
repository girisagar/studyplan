from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("curriculum", "0010_chapter_course_required"),
        ("library", "0002_book_to_resource"),
    ]

    operations = [
        migrations.RenameField("course", "books", "resources"),
        migrations.AlterField(
            model_name="course",
            name="resources",
            field=models.ManyToManyField(
                blank=True, related_name="courses", to="library.resource"
            ),
        ),
        migrations.AddField(
            model_name="chapter",
            name="resources",
            field=models.ManyToManyField(
                blank=True, related_name="chapters", to="library.resource"
            ),
        ),
    ]
