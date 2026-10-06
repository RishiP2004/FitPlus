"""PB-08: create and edit fitness profile, kg/lb units."""
from app.profile import get_profile
from tests.base import AppTestCase

GOOD = {"unit_system": "metric", "age": "25", "weight": "70", "height": "175",
        "fitness_level": "Beginner", "goal": "Build muscle"}


class ProfileTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.uid = self.user()["id"]

    def test_profile_saved(self):
        r = self.post("/profile/", GOOD)
        self.assertEqual(r.status_code, 302)
        p = get_profile(self.uid)
        self.assertEqual(p["age"], 25)
        self.assertAlmostEqual(p["weight_kg"], 70)
        self.assertAlmostEqual(p["height_cm"], 175)
        self.assertEqual(p["fitness_level"], "Beginner")
        self.assertEqual(p["goal"], "Build muscle")

    def test_profile_editable_later(self):
        self.post("/profile/", GOOD)
        self.post("/profile/", {**GOOD, "age": "26", "goal": "Get stronger"})
        p = get_profile(self.uid)
        self.assertEqual(p["age"], 26)
        self.assertEqual(p["goal"], "Get stronger")

    def test_pounds_and_inches_converted(self):
        self.post("/profile/", {**GOOD, "unit_system": "imperial", "weight": "154.3", "height": "69"})
        p = get_profile(self.uid)
        self.assertAlmostEqual(p["weight_kg"], 70.0, delta=0.1)
        self.assertAlmostEqual(p["height_cm"], 175.3, delta=0.1)
        page = self.client.get("/profile/").data
        self.assertIn(b"154.3", page)
        self.assertIn(b"lb", page)

    def test_invalid_values_rejected(self):
        for field, value in [("age", "5"), ("weight", "abc"), ("height", ""),
                             ("fitness_level", "Pro"), ("goal", "x")]:
            r = self.post("/profile/", {**GOOD, field: value})
            self.assertEqual(r.status_code, 400, field)
        self.assertIsNone(get_profile(self.uid))

    def test_dashboard_shows_profile(self):
        self.post("/profile/", GOOD)
        page = self.client.get("/dashboard").data
        self.assertIn(b"Build muscle", page)
        self.assertIn(b"70.0 kg", page)
