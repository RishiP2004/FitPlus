"""Shared test setup: a fresh app + SQLite database per test."""
import os
import tempfile
import unittest

from app import create_app
from app.db import query_one

CSRF = "test-csrf-token"


def _reset_postgres(url):
    import psycopg

    with psycopg.connect(url, autocommit=True) as conn:
        conn.execute("DROP SCHEMA public CASCADE")
        conn.execute("CREATE SCHEMA public")


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test",
            # CI also runs the suite against PostgreSQL by setting TEST_DATABASE_URL.
            "DATABASE_URL": os.environ.get("TEST_DATABASE_URL", ""),
            "DATABASE_PATH": os.path.join(self.tmp.name, "test.sqlite3"),
        })
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

    def tearDown(self):
        self.ctx.pop()
        if self.app.config["DATABASE_URL"]:
            _reset_postgres(self.app.config["DATABASE_URL"])
        self.tmp.cleanup()

    # ------------------------------------------------------------ helpers
    def _csrf(self):
        with self.client.session_transaction() as s:
            s["_csrf"] = CSRF

    def post(self, url, data=None, **kw):
        self._csrf()
        data = dict(data or {})
        data.setdefault("csrf_token", CSRF)
        return self.client.post(url, data=data, **kw)

    def register(self, email="ana@example.com", password="secret123", confirm=None):
        return self.post("/register", {
            "email": email, "password": password,
            "confirm": password if confirm is None else confirm,
        })

    def login(self, email="ana@example.com", password="secret123", **extra):
        return self.post("/login", {"email": email, "password": password, **extra})

    def logout(self):
        return self.post("/logout")

    def user(self, email="ana@example.com"):
        return query_one("SELECT * FROM users WHERE email = ?", (email,))
