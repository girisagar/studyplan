from config.testing import APITestCase
from progress.models import UserRoadMap, UserTopicProgress


class RoadMapAPITests(APITestCase):
    def test_list_anonymous(self):
        data = self.get("/roadmaps").json()
        self.assertEqual(len(data), 1)
        roadmap = data[0]
        self.assertEqual((roadmap["topic_count"], roadmap["hours"]), (3, 9))
        self.assertEqual(roadmap["weeks"], 2)
        self.assertFalse(roadmap["following"])
        self.assertIsNone(roadmap["progress"])
        # Rich text is sanitized.
        self.assertNotIn("<script", roadmap["description"])
        self.assertIn("<strong>it</strong>", roadmap["description"])

    def test_list_following(self):
        UserRoadMap.objects.create(user=self.user, roadmap=self.roadmap)
        UserTopicProgress.objects.create(user=self.user, topic=self.a)
        roadmap = self.get("/roadmaps", self.user).json()[0]
        self.assertTrue(roadmap["following"])
        self.assertEqual(
            roadmap["progress"], {"completed": 1, "total": 3, "percent": 33}
        )
        self.assertEqual(roadmap["next_item"]["topic"]["id"], self.b.pk)

    def test_detail(self):
        UserRoadMap.objects.create(user=self.user, roadmap=self.roadmap)
        UserTopicProgress.objects.create(user=self.user, topic=self.a)
        data = self.get(f"/roadmaps/{self.roadmap.pk}", self.user).json()
        self.assertEqual(data["finish"], "progress")
        self.assertEqual(data["enrollment"]["roadmap_id"], self.roadmap.pk)
        self.assertEqual(data["schedule"][0]["state"], "current")
        self.assertEqual(
            data["schedule"][0]["course"]["resources"][0]["title"], self.book.title
        )
        self.assertEqual([s["week"] for s in data["sections"]], [1, 2])
        group = data["sections"][0]["groups"][0]
        self.assertEqual((group["completed"], group["percent"]), (1, 50))
        self.assertEqual(group["chapter"]["position"], 1)
        self.assertEqual(
            data["resources"][0]["file_url"], "http://testserver/media/books/intro.pdf"
        )

    def test_detail_404(self):
        self.assertEqual(self.get("/roadmaps/999").status_code, 404)

    def test_course_player_resumes_at_first_unfinished(self):
        UserTopicProgress.objects.create(user=self.user, topic=self.a)
        url = f"/roadmaps/{self.roadmap.pk}/courses/{self.course.pk}"
        data = self.get(url, self.user).json()
        self.assertEqual(data["current"]["topic"]["id"], self.b.pk)
        self.assertEqual(data["previous"]["topic"]["id"], self.a.pk)
        self.assertEqual(data["next"]["topic"]["id"], self.c.pk)
        self.assertEqual(data["current"]["topic"]["resources"][0]["kind"], "video")
        self.assertEqual(data["placement"]["first_week"], 1)
        self.assertIsNone(data["progress"])  # not following
        week2 = self.get(f"{url}?week=2").json()
        self.assertEqual(week2["current"]["topic"]["id"], self.c.pk)
        self.assertEqual(self.get(f"{url}?week=9").status_code, 404)

    def test_topic_panel_and_shortcuts(self):
        base = f"/roadmaps/{self.roadmap.pk}"
        panel = self.get(f"{base}/courses/{self.course.pk}/topics/{self.c.pk}").json()
        self.assertEqual(panel["current"]["topic"]["id"], self.c.pk)
        self.assertNotIn("sections", panel)
        self.assertEqual(
            self.get(f"{base}/topics/{self.b.pk}").json()["current"]["number"], 2
        )
        self.assertEqual(
            self.get(f"{base}/weeks/2").json()["current"]["topic"]["id"], self.c.pk
        )
        self.assertEqual(self.get(f"{base}/weeks/5").status_code, 404)
        self.assertEqual(self.get(f"{base}/topics/999").status_code, 404)

    def test_expired_token_is_rejected_not_anonymous(self):
        response = self.client.get(
            "/api/roadmaps", HTTP_AUTHORIZATION="Bearer expired.or.bad"
        )
        self.assertEqual(response.status_code, 401)


class RoadMapStateTests(APITestCase):
    def follow(self, days_ago=0):
        from datetime import timedelta
        from django.utils import timezone

        return UserRoadMap.objects.create(
            user=self.user,
            roadmap=self.roadmap,
            started_at=timezone.now() - timedelta(days=days_ago),
        )

    def test_finished_roadmap(self):
        self.follow()
        for topic in (self.a, self.b, self.c):
            UserTopicProgress.objects.create(user=self.user, topic=topic)
        data = self.get(f"/roadmaps/{self.roadmap.pk}", self.user).json()
        self.assertEqual(data["finish"], "complete")
        self.assertIsNone(data["next_item"])
        self.assertEqual(data["schedule"][0]["state"], "done")
        active = self.get("/progress/dashboard", self.user).json()["active"]
        self.assertEqual(active["pace"], "done")

    def test_behind_schedule(self):
        self.follow(days_ago=10)  # schedule expects week 2, next topic is in week 1
        active = self.get("/progress/dashboard", self.user).json()["active"]
        self.assertEqual((active["scheduled_week"], active["pace"]), (2, "behind"))

    def test_other_users_progress_is_not_shown(self):
        self.follow()
        UserTopicProgress.objects.create(user=self.other, topic=self.a)
        data = self.get(f"/roadmaps/{self.roadmap.pk}", self.user).json()
        self.assertEqual(data["progress"]["completed"], 0)
        self.assertFalse(data["sections"][0]["groups"][0]["items"][0]["completed"])
