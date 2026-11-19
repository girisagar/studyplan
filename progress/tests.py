from config.testing import APITestCase
from progress.models import UserRoadMap, UserTopicProgress


class ProgressAPITests(APITestCase):
    def completion(self, topic, completed, user=None, roadmap=None):
        roadmap = roadmap or self.roadmap.pk
        return self.send(
            "put",
            f"/progress/roadmaps/{roadmap}/topics/{topic.pk}/completion",
            {"completed": completed},
            user=user or self.user,
        )

    def test_requires_auth(self):
        for path in (
            "/progress/enrollments",
            "/progress/dashboard",
            "/progress/overview",
        ):
            self.assertEqual(self.get(path).status_code, 401, path)

    def test_enroll_is_idempotent(self):
        path = f"/progress/roadmaps/{self.roadmap.pk}/enrollment"
        first = self.send("put", path, user=self.user).json()
        second = self.send("put", path, user=self.user).json()
        self.assertEqual(first, second)
        self.assertEqual(first["roadmap_name"], "Quant path")
        self.assertEqual(UserRoadMap.objects.count(), 1)
        self.assertEqual(len(self.get("/progress/enrollments", self.user).json()), 1)
        self.assertEqual(
            self.send(
                "put", "/progress/roadmaps/999/enrollment", user=self.user
            ).status_code,
            404,
        )

    def test_completion(self):
        self.assertEqual(
            self.completion(self.a, True).status_code, 404
        )  # not following
        UserRoadMap.objects.create(user=self.user, roadmap=self.roadmap)
        data = self.completion(self.a, True).json()
        self.assertEqual(data["completed"], True)
        self.assertEqual(data["progress"]["completed"], 1)
        self.assertEqual(data["course"]["total"], 3)
        self.completion(self.a, True)  # idempotent
        self.assertEqual(UserTopicProgress.objects.count(), 1)
        self.assertEqual(
            self.completion(self.a, False).json()["progress"]["completed"], 0
        )
        self.assertFalse(UserTopicProgress.objects.exists())
        self.assertEqual(self.completion(self.a, True, roadmap=999).status_code, 404)

    def test_roadmap_progress(self):
        UserRoadMap.objects.create(user=self.user, roadmap=self.roadmap)
        UserTopicProgress.objects.create(user=self.user, topic=self.c)
        data = self.get("/progress/roadmaps", self.user).json()
        self.assertEqual(
            data,
            [
                {
                    "roadmap_id": self.roadmap.pk,
                    "completed": 1,
                    "total": 3,
                    "percent": 33,
                }
            ],
        )

    def test_dashboard(self):
        data = self.get("/progress/dashboard", self.user).json()
        self.assertIsNone(data["active"])
        self.assertEqual(len(data["roadmaps"]), 1)
        UserRoadMap.objects.create(user=self.user, roadmap=self.roadmap)
        UserTopicProgress.objects.create(user=self.user, topic=self.a)
        data = self.get("/progress/dashboard", self.user).json()
        self.assertEqual(data["active"]["next"]["topic"]["id"], self.b.pk)
        self.assertEqual(data["active"]["pace"], "on_track")
        self.assertEqual(
            data["stats"],
            {"completed": 1, "this_week": 1, "hours_done": 2, "following": 1},
        )
        self.assertEqual(
            {m["title"] for m in data["materials"]},
            {"Lecture video", "Intro to Probability"},
        )
        self.assertEqual(data["roadmaps"], [])

    def test_overview(self):
        UserRoadMap.objects.create(user=self.user, roadmap=self.roadmap)
        UserTopicProgress.objects.create(user=self.user, topic=self.a)
        UserTopicProgress.objects.create(user=self.other, topic=self.b)
        data = self.get("/progress/overview", self.user).json()
        self.assertEqual(
            data["snapshots"][0]["schedule"][0]["progress"]["completed"], 1
        )
        self.assertEqual([r["topic"]["id"] for r in data["recent"]], [self.a.pk])
        self.assertEqual(data["recent"][0]["roadmap_id"], self.roadmap.pk)
        self.assertEqual(len(data["weeks"]), 8)
        self.assertEqual(data["weeks"][-1]["count"], 1)
