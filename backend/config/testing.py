"""Helpers for REST API tests."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from ninja_jwt.tokens import RefreshToken

from curriculum.models import Chapter, Course, Tag, Topic
from library.models import Resource
from roadmaps.models import RoadMap, RoadMapCourse


class APITestCase(TestCase):
    """A one-course roadmap: week 1 has topics A and B, week 2 has topic C."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user("learner", password="test-password")
        cls.other = User.objects.create_user("other", password="test-password")
        cls.course = Course.objects.create(name="Probability")
        cls.week1 = Chapter.objects.create(course=cls.course, week=1, name="Counting")
        cls.week2 = Chapter.objects.create(course=cls.course, week=2, name="Bayes")
        cls.a = Topic.objects.create(
            chapter=cls.week1, topic_name="Topic A", total_time=2, order=1
        )
        cls.b = Topic.objects.create(
            chapter=cls.week1, topic_name="Topic B", total_time=3, order=2
        )
        cls.c = Topic.objects.create(
            chapter=cls.week2, topic_name="Topic C", total_time=4
        )
        cls.a.tags.add(Tag.objects.create(name="theory"))
        cls.book = Resource.objects.create(
            title="Intro to Probability", author="Blitzstein", file="books/intro.pdf"
        )
        cls.video = Resource.objects.create(
            title="Lecture video", kind="video", url="https://example.com/v"
        )
        cls.course.resources.add(cls.book)
        cls.b.resources.add(cls.video)
        cls.roadmap = RoadMap.objects.create(
            name="Quant path",
            description="<p>Learn <strong>it</strong><script>alert(1)</script></p>",
        )
        RoadMapCourse.objects.create(roadmap=cls.roadmap, course=cls.course)

    def auth(self, user=None):
        token = RefreshToken.for_user(user or self.user).access_token
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    def get(self, path, user=None, **extra):
        headers = self.auth(user) if user else {}
        return self.client.get(f"/api{path}", **headers, **extra)

    def send(self, method, path, data=None, user=None):
        headers = self.auth(user) if user else {}
        body = (
            {} if data is None else {"data": data, "content_type": "application/json"}
        )
        return getattr(self.client, method)(f"/api{path}", **body, **headers)
