from django.contrib.auth.models import Permission

from config.testing import APITestCase


class CurriculumAPITests(APITestCase):
    def test_course_detail(self):
        data = self.get(f"/curriculum/courses/{self.course.pk}").json()
        self.assertEqual([c["name"] for c in data["chapters"]], ["Counting", "Bayes"])
        self.assertEqual(
            [t["topic_name"] for t in data["chapters"][0]["topics"]],
            ["Topic A", "Topic B"],
        )
        self.assertEqual(data["chapters"][0]["topics"][0]["tags"][0]["name"], "theory")

    def test_topic(self):
        data = self.get(f"/curriculum/topics/{self.b.pk}").json()
        self.assertEqual(data["chapter"]["name"], "Counting")
        self.assertEqual(data["course"]["id"], self.course.pk)
        self.assertEqual(data["resources"][0]["href"], "https://example.com/v")
        self.assertEqual(self.get("/curriculum/topics/999").status_code, 404)

    def test_edit_description_needs_permission(self):
        path = f"/curriculum/topics/{self.a.pk}/description"
        body = {"description": "<p>New</p>"}
        self.assertEqual(self.send("put", path, body).status_code, 401)
        self.assertEqual(self.send("put", path, body, user=self.user).status_code, 403)
        self.user.user_permissions.add(Permission.objects.get(codename="change_topic"))
        response = self.send("put", path, body, user=self.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["description"], "<p>New</p>")
        self.assertTrue(self.get("/auth/me", self.user).json()["can_edit_topics"])
