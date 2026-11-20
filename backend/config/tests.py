from config.testing import APITestCase


class PrivateAPIResponseTests(APITestCase):
    def test_requests_with_credentials_are_private(self):
        response = self.get("/roadmaps", self.user)
        self.assertIn("private", response["Cache-Control"])

    def test_anonymous_requests_are_not_marked(self):
        self.assertFalse(self.get("/roadmaps").has_header("Cache-Control"))

    def test_html_routes_are_gone(self):
        for path in ("/", "/roadmaps/", "/accounts/login/", "/service-worker.js"):
            self.assertEqual(self.client.get(path).status_code, 404, path)
