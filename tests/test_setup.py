"""PB-03: database live, hosting health check, starter page."""
from tests.base import AppTestCase


class SetupTests(AppTestCase):
    def test_starter_page_loads(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"FitPlus", r.data)

    def test_health_reports_database_ok(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        body = r.get_json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["database"], "ok")
        self.assertGreaterEqual(body["preset_exercises"], 50)

    def test_security_headers_present(self):
        r = self.client.get("/")
        self.assertEqual(r.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(r.headers["X-Frame-Options"], "DENY")

    def test_unknown_page_is_404(self):
        self.assertEqual(self.client.get("/nope").status_code, 404)
