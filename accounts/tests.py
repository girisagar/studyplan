from config.testing import APITestCase
from progress.models import UserRoadMap


class AuthAPITests(APITestCase):
    def login(self, password="test-password"):
        return self.send(
            "post", "/auth/login", {"username": "learner", "password": password}
        )

    def test_login_returns_tokens_and_user(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["user"]["username"], "learner")
        me = self.client.get(
            "/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {data['access']}"
        )
        self.assertEqual(me.json()["id"], self.user.pk)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_login)

    def test_bad_credentials(self):
        self.assertEqual(self.login("wrong").status_code, 401)

    def test_me_requires_token(self):
        self.assertEqual(self.get("/auth/me").status_code, 401)
        bad = self.client.get("/api/auth/me", HTTP_AUTHORIZATION="Bearer nope")
        self.assertEqual(bad.status_code, 401)
        self.assertIn("detail", bad.json())

    def test_session_cookie_is_not_api_auth(self):
        UserRoadMap.objects.create(user=self.user, roadmap=self.roadmap)
        self.assertIsNotNone(self.get("/roadmaps", self.user).json()[0]["progress"])
        self.client.force_login(self.user)
        self.assertEqual(self.get("/auth/me").status_code, 401)
        # Optional-auth endpoints treat a session-only request as signed out.
        self.assertIsNone(self.get("/roadmaps").json()[0]["progress"])

    def test_register(self):
        response = self.send(
            "post",
            "/auth/register",
            {
                "username": "new",
                "password1": "a-Long-pass-91",
                "password2": "a-Long-pass-91",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["user"]["username"], "new")

    def test_register_validation(self):
        response = self.send(
            "post",
            "/auth/register",
            {"username": "learner", "password1": "123", "password2": "456"},
        )
        self.assertEqual(response.status_code, 422)
        fields = {e["loc"][-1] for e in response.json()["detail"]}
        self.assertEqual(fields, {"username", "password2"})

    def test_refresh_rotates_and_blacklists(self):
        refresh = self.login().json()["refresh"]
        response = self.send("post", "/auth/refresh", {"refresh": refresh})
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()["refresh"], refresh)
        again = self.send("post", "/auth/refresh", {"refresh": refresh})
        self.assertEqual(again.status_code, 401)

    def test_logout_revokes_refresh_token(self):
        refresh = self.login().json()["refresh"]
        self.assertEqual(
            self.send("post", "/auth/logout", {"refresh": refresh}).status_code, 204
        )
        self.assertEqual(
            self.send("post", "/auth/refresh", {"refresh": refresh}).status_code, 401
        )
        # Idempotent.
        self.assertEqual(
            self.send("post", "/auth/logout", {"refresh": refresh}).status_code, 204
        )

    def test_inactive_user_cannot_refresh(self):
        refresh = self.login().json()["refresh"]
        self.user.is_active = False
        self.user.save()
        self.assertEqual(
            self.send("post", "/auth/refresh", {"refresh": refresh}).status_code, 401
        )
