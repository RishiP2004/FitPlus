"""PB-09 seed, PB-10 browse, PB-11 detail, PB-12 search, PB-13 filter."""
import time

from app.db import query_all, query_one
from app.exercises import search_exercises
from app.seed import seed_exercises
from tests.base import AppTestCase


class ExerciseTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.register()

    # PB-09
    def test_at_least_50_exercises_seeded_with_all_fields(self):
        rows = query_all("SELECT * FROM exercises WHERE created_by IS NULL")
        self.assertGreaterEqual(len(rows), 50)
        for r in rows:
            for field in ("name", "muscle_group", "equipment", "instructions"):
                self.assertTrue(r[field], (r["name"], field))

    def test_seeding_is_idempotent(self):
        before = len(query_all("SELECT id FROM exercises"))
        self.assertEqual(seed_exercises(), 0)
        self.assertEqual(len(query_all("SELECT id FROM exercises")), before)

    # PB-10
    def test_browse_grouped_by_muscle_group(self):
        page = self.client.get("/exercises/").data.decode()
        for group in ["Chest", "Back", "Shoulders", "Core"]:
            self.assertIn(f"<h2>{group}</h2>", page)
        self.assertIn("Barbell Bench Press", page)
        self.assertLess(page.index("<h2>Chest</h2>"), page.index("<h2>Back</h2>"))

    # PB-11
    def test_detail_shows_instructions_muscle_and_equipment(self):
        ex = query_one("SELECT * FROM exercises WHERE name = ?", ("Deadlift",))
        page = self.client.get(f"/exercises/{ex['id']}").data.decode()
        self.assertIn("Deadlift", page)
        self.assertIn("Back", page)
        self.assertIn("Barbell", page)
        self.assertIn("How to do it", page)
        self.assertIn("flat back", page)

    def test_missing_exercise_is_404(self):
        self.assertEqual(self.client.get("/exercises/99999").status_code, 404)

    # PB-12
    def test_search_by_name_case_insensitive(self):
        names = [r["name"] for r in search_exercises(q="SQUAT")]
        self.assertTrue(names)
        self.assertTrue(all("squat" in n.lower() for n in names))

    def test_search_page_hides_non_matches(self):
        page = self.client.get("/exercises/?q=deadlift").data.decode()
        self.assertIn('exercise" data-name="deadlift"', page.replace("  ", " "))
        bench = page.split('data-name="barbell bench press"')[1].split(">")[0]
        self.assertIn("hidden", bench)

    def test_search_is_fast(self):
        start = time.perf_counter()
        r = self.client.get("/exercises/?q=press&muscle=Chest")
        self.assertEqual(r.status_code, 200)
        self.assertLess(time.perf_counter() - start, 1.0)

    # PB-13
    def test_filter_by_muscle_group(self):
        rows = search_exercises(muscle="Back")
        self.assertTrue(rows)
        self.assertTrue(all(r["muscle_group"] == "Back" for r in rows))

    def test_filter_by_equipment(self):
        rows = search_exercises(equipment="Dumbbell")
        self.assertTrue(rows)
        self.assertTrue(all(r["equipment"] == "Dumbbell" for r in rows))

    def test_filters_combine_with_search(self):
        rows = search_exercises(q="press", muscle="Chest", equipment="Dumbbell")
        self.assertTrue(rows)
        for r in rows:
            self.assertIn("press", r["name"].lower())
            self.assertEqual((r["muscle_group"], r["equipment"]), ("Chest", "Dumbbell"))

    def test_no_results_message(self):
        page = self.client.get("/exercises/?q=zzzz").data.decode()
        self.assertIn("0 exercises", page)
        self.assertIn('id="no-results" class="empty" >', page.replace("  ", " "))

    def test_library_requires_login(self):
        self.logout()
        self.assertEqual(self.client.get("/exercises/").status_code, 302)
