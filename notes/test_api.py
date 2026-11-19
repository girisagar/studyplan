from config.testing import APITestCase
from notes.models import Note


class NotesAPITests(APITestCase):
    def target(self):
        return f"/notes/curriculum/topic/{self.a.pk}"

    def test_requires_auth(self):
        self.assertEqual(self.get(self.target()).status_code, 401)

    def test_crud(self):
        created = self.send(
            "post",
            self.target(),
            {"title": " Idea ", "body": "<p>Hi<script>x()</script></p>"},
            user=self.user,
        )
        self.assertEqual(created.status_code, 201)
        note = created.json()
        self.assertEqual(note["title"], "Idea")
        self.assertEqual(note["body"], "<p>Hi</p>")
        self.assertEqual((note["app_label"], note["model"]), ("curriculum", "topic"))
        listing = self.get(self.target(), self.user).json()
        self.assertEqual(listing["target"]["title"], "Topic A")
        self.assertEqual(len(listing["notes"]), 1)
        updated = self.send(
            "put", f"/notes/{note['id']}", {"body": "<p>New</p>"}, user=self.user
        )
        self.assertEqual(updated.json()["body"], "<p>New</p>")
        self.assertEqual(
            self.send("delete", f"/notes/{note['id']}", user=self.user).status_code, 204
        )
        self.assertFalse(Note.objects.exists())

    def test_note_counts_in_content(self):
        self.send("post", self.target(), {"body": "<p>x</p>"}, user=self.user)
        topic = self.get(f"/curriculum/topics/{self.a.pk}", self.user).json()
        self.assertEqual(topic["note_count"], 1)
        self.assertEqual(
            self.get(f"/curriculum/topics/{self.a.pk}", self.other).json()[
                "note_count"
            ],
            0,
        )

    def test_validation_and_targets(self):
        empty = self.send("post", self.target(), {"body": "<p> </p>"}, user=self.user)
        self.assertEqual(empty.status_code, 422)
        for path in ("/notes/auth/user/1", "/notes/curriculum/topic/999"):
            self.assertEqual(self.get(path, self.user).status_code, 404, path)

    def test_notes_are_private(self):
        note = self.send(
            "post", self.target(), {"body": "<p>x</p>"}, user=self.user
        ).json()
        self.assertEqual(self.get(f"/notes/{note['id']}", self.other).status_code, 404)
        self.assertEqual(
            self.send("delete", f"/notes/{note['id']}", user=self.other).status_code,
            404,
        )
        self.assertEqual(self.get(self.target(), self.other).json()["notes"], [])
