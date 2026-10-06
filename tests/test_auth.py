"""PB-04 registration, PB-05 password storage/duplicates, PB-06 login, PB-07 logout."""
from tests.base import AppTestCase


class RegistrationTests(AppTestCase):  # PB-04
    def test_valid_registration_creates_account_and_logs_in(self):
        r = self.register()
        self.assertEqual(r.status_code, 302)
        self.assertIn("/profile", r.headers["Location"])
        self.assertIsNotNone(self.user())
        self.assertEqual(self.client.get("/dashboard").status_code, 200)

    def test_email_is_normalised(self):
        self.register(email="  Ana@Example.COM ")
        self.assertIsNotNone(self.user("ana@example.com"))

    def test_invalid_email_rejected(self):
        for bad in ["", "ana", "ana@", "ana@example", "a b@example.com"]:
            r = self.register(email=bad)
            self.assertEqual(r.status_code, 400, bad)
        self.assertIsNone(self.user("ana"))

    def test_password_must_be_8_chars(self):
        r = self.register(password="short7!")
        self.assertEqual(r.status_code, 400)
        self.assertIn(b"at least 8 characters", r.data)
        self.assertIsNone(self.user())

    def test_passwords_must_match(self):
        r = self.register(confirm="different1")
        self.assertEqual(r.status_code, 400)
        self.assertIn(b"do not match", r.data)


class PasswordStorageTests(AppTestCase):  # PB-05
    def test_password_stored_as_bcrypt_hash(self):
        self.register()
        stored = self.user()["password_hash"]
        self.assertNotEqual(stored, "secret123")
        self.assertTrue(stored.startswith("$2"), stored)

    def test_duplicate_email_rejected_with_message(self):
        self.register()
        self.logout()
        r = self.register(email="ANA@example.com")
        self.assertEqual(r.status_code, 400)
        self.assertIn(b"already exists", r.data)


class LoginTests(AppTestCase):  # PB-06
    def setUp(self):
        super().setUp()
        self.register()
        self.logout()

    def test_correct_credentials_open_dashboard(self):
        r = self.login()
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.headers["Location"].endswith("/dashboard"))
        self.assertIn(b"Dashboard", self.client.get("/dashboard").data)

    def test_wrong_password_shows_error(self):
        r = self.login(password="wrongpass")
        self.assertEqual(r.status_code, 401)
        self.assertIn(b"Incorrect email or password", r.data)

    def test_unknown_email_shows_same_error(self):
        r = self.login(email="nobody@example.com")
        self.assertEqual(r.status_code, 401)
        self.assertIn(b"Incorrect email or password", r.data)

    def test_next_redirect_only_to_own_site(self):
        r = self.login(next="https://evil.example.com/")
        self.assertTrue(r.headers["Location"].endswith("/dashboard"))
        self.logout()
        r = self.login(next="/exercises/")
        self.assertTrue(r.headers["Location"].endswith("/exercises/"))

    def test_form_without_csrf_token_rejected(self):
        r = self.client.post("/login", data={"email": "ana@example.com", "password": "secret123"})
        self.assertEqual(r.status_code, 400)


class LogoutTests(AppTestCase):  # PB-07
    def test_logout_ends_session_and_protects_pages(self):
        self.register()
        r = self.logout()
        self.assertEqual(r.status_code, 302)
        for page in ["/dashboard", "/profile/", "/exercises/"]:
            r = self.client.get(page)
            self.assertEqual(r.status_code, 302, page)
            self.assertIn("/login", r.headers["Location"])

    def test_logout_requires_post(self):
        self.assertEqual(self.client.get("/logout").status_code, 405)
