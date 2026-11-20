from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from config.testing import APITestCase
from curriculum.models import Topic
from .models import Note
from .services import attach_note_counts


class NoteModelTests(APITestCase):
    def make_note(self, target=None, user=None, **kwargs):
        return Note.objects.create(
            content_object=target or self.a,
            created_by=user or self.user,
            body=kwargs.pop("body", "My study note"),
            **kwargs,
        )

    def test_model_validates_supported_existing_target(self):
        invalid = Note(content_object=self.user, created_by=self.user, body="Invalid")
        with self.assertRaises(ValidationError):
            invalid.full_clean()
        missing = Note(
            content_type=ContentType.objects.get_for_model(Topic),
            object_id=99999,
            created_by=self.user,
            body="Missing",
        )
        with self.assertRaises(ValidationError):
            missing.full_clean()

    def test_rich_text_preserves_formatting_and_removes_unsafe_html(self):
        body = (
            "<h2>Summary</h2><p><strong>Bold</strong> and <em>italic</em></p>"
            "<ul><li>First</li></ul><blockquote><p>Quote</p></blockquote>"
            '<pre><code class="language-python">x = 1</code></pre>'
            '<p><a href="https://example.com">Reference</a></p>'
            '<script>alert(1)</script><img src="x" onerror="alert(1)">'
            '<p onclick="alert(1)"><a href="javascript:alert(1)">Bad link</a></p>'
        )
        path = f"/notes/curriculum/topic/{self.a.pk}"
        response = self.send("post", path, {"body": body}, user=self.user)
        self.assertEqual(response.status_code, 201)
        stored = Note.objects.get().body
        for fragment in [
            "<h2>Summary</h2>",
            "<strong>Bold</strong>",
            "<em>italic</em>",
            "<li>First</li>",
            "<blockquote>",
            '<pre><code class="language-python">',
            'href="https://example.com"',
        ]:
            self.assertIn(fragment, stored)
        for fragment in ["<script", "onerror", "onclick", "javascript:", "<img"]:
            self.assertNotIn(fragment, stored)

    def test_empty_rich_text_is_rejected(self):
        path = f"/notes/curriculum/topic/{self.a.pk}"
        for body in ["<p>&nbsp;</p>", "<p><br></p>", "<script>alert(1)</script>"]:
            response = self.send("post", path, {"body": body}, user=self.user)
            self.assertEqual(response.status_code, 422)
            self.assertIn("Write some text", response.content.decode())
        self.assertFalse(Note.objects.exists())

    def test_stored_html_is_sanitized_on_output(self):
        note = self.make_note(body="<p>ok</p><script>alert(1)</script>")
        data = self.get(f"/notes/{note.pk}", self.user).json()
        self.assertEqual(data["body"], "<p>ok</p>")

    def test_legacy_note_migration_preserves_literal_text_and_linebreaks(self):
        from importlib import import_module
        from django.apps import apps
        from django.db import connection

        note = self.make_note(
            body="<strong>Literal markup</strong> & text\nNext line\n\nParagraph"
        )
        migration = import_module("notes.migrations.0002_alter_note_body")
        migration.wrap_plain_text(apps, connection.schema_editor())
        note.refresh_from_db()
        self.assertEqual(
            note.body,
            "<p>&lt;strong&gt;Literal markup&lt;/strong&gt; &amp; text<br>Next line</p>\n\n<p>Paragraph</p>",
        )

    def test_counts_are_private_and_batched(self):
        self.make_note()
        self.make_note(user=self.other)
        # Separate instances of the same topic, as repeated outline rows have.
        instances = [Topic.objects.get(pk=self.a.pk) for _ in range(5)]
        ContentType.objects.get_for_model(Topic)
        with self.assertNumQueries(1):
            attach_note_counts(instances, self.user)
        self.assertEqual([obj.note_count for obj in instances], [1] * 5)

    def test_target_deletion_cleans_up_notes(self):
        note = self.make_note()
        self.a.delete()
        self.assertFalse(Note.objects.filter(pk=note.pk).exists())
