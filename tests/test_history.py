"""PB-21 history list, PB-22 date filter, PB-26 body weight."""
from datetime import datetime, timedelta

from app.db import execute, query_all
from app.util import local_today
from tests.sprint2 import Sprint2Case


class HistoryTests(Sprint2Case):  # PB-21
    def test_sorted_newest_first(self):
        old, _ = self.finished_workout("Deadlift")
        new, _ = self.finished_workout("Pull-Up", reps=8, weight=0)
        execute("UPDATE workout_sessions SET name = 'Older' WHERE id = ?", (old,))
        execute("UPDATE workout_sessions SET name = 'Newer' WHERE id = ?", (new,))
        execute("UPDATE workout_sessions SET started_at = ? WHERE id = ?",
                (datetime(2026, 10, 1, 15), old))
        page = self.client.get("/history").data.decode()
        self.assertLess(page.index("Newer"), page.index("Older"))
        self.assertIn("2 workouts", page)

    def test_open_session_shows_all_sets(self):
        sid, item = self.finished_workout(weight=100)
        self.add_set(sid, item, 4, 110)
        page = self.client.get("/history").data.decode()
        self.assertIn(f"/workouts/{sid}", page)
        detail = self.client.get(f"/workouts/{sid}").data.decode()
        self.assertIn("<td>100</td>", detail)
        self.assertIn("<td>110</td>", detail)

    def test_unfinished_workouts_not_in_history(self):
        self.start()
        self.assertIn(b"0 workouts", self.client.get("/history").data)

    def test_other_users_workouts_hidden(self):
        sid, _ = self.finished_workout()
        self.logout()
        self.register(email="bob@example.com")
        self.assertIn(b"0 workouts", self.client.get("/history").data)
        self.assertEqual(self.client.get(f"/workouts/{sid}").status_code, 404)


class HistoryFilterTests(Sprint2Case):  # PB-22
    def setUp(self):
        super().setUp()
        dates = {"Sep": datetime(2026, 9, 15, 16), "Early Oct": datetime(2026, 10, 2, 16),
                 "Mid Oct": datetime(2026, 10, 14, 16)}
        for name, when in dates.items():
            sid, _ = self.finished_workout()
            execute("UPDATE workout_sessions SET name = ?, started_at = ? WHERE id = ?",
                    (name, when, sid))

    def test_filter_by_date_range(self):
        page = self.client.get("/history?from=2026-10-01&to=2026-10-10").data.decode()
        self.assertIn("Early Oct", page)
        self.assertNotIn("Mid Oct", page)
        self.assertNotIn(">Sep<", page)
        self.assertIn("1 workout in this date range", page)

    def test_open_ended_ranges(self):
        page = self.client.get("/history?from=2026-10-01").data.decode()
        self.assertIn("Mid Oct", page)
        self.assertNotIn(">Sep<", page)
        page = self.client.get("/history?to=2026-09-30").data.decode()
        self.assertIn(">Sep<", page)
        self.assertNotIn("Early Oct", page)

    def test_local_day_boundary(self):
        # 11:30 PM Toronto on Oct 10 is 03:30 UTC on Oct 11; it belongs to Oct 10.
        sid, _ = self.finished_workout()
        execute("UPDATE workout_sessions SET name = 'Late', started_at = ? WHERE id = ?",
                (datetime(2026, 10, 11, 3, 30), sid))
        self.assertIn("Late", self.client.get("/history?from=2026-10-10&to=2026-10-10").data.decode())
        self.assertNotIn("Late", self.client.get("/history?from=2026-10-11&to=2026-10-11").data.decode())

    def test_invalid_range_rejected(self):
        r = self.client.get("/history?from=2026-10-10&to=2026-10-01")
        self.assertEqual(r.status_code, 400)
        self.assertIn(b"on or after the start date", r.data)
        self.assertEqual(self.client.get("/history?from=nope").status_code, 400)


class BodyWeightTests(Sprint2Case):  # PB-26
    def log(self, day, weight):
        return self.post("/body-weight", {"entry_date": day, "weight": weight})

    def entries(self):
        return query_all("SELECT * FROM body_weights ORDER BY entry_date")

    def test_log_and_list_newest_first(self):
        self.log("2026-10-01", "80.5")
        self.log("2026-10-08", "79.9")
        self.assertEqual([e["weight_kg"] for e in self.entries()], [80.5, 79.9])
        page = self.client.get("/body-weight").data.decode()
        self.assertLess(page.index("79.9"), page.index("80.5"))
        self.assertIn("79.9", self.client.get("/history").data.decode())

    def test_one_entry_per_date(self):
        self.log("2026-10-01", "80")
        r = self.log("2026-10-01", "81")
        self.assertEqual(r.status_code, 400)
        self.assertIn(b"already logged a weight for this date", r.data)
        self.assertEqual(len(self.entries()), 1)

    def test_validation(self):
        future = (local_today() + timedelta(days=2)).isoformat()
        for day, weight in [(future, "80"), ("bad", "80"), ("2026-10-01", "5"), ("2026-10-01", "x")]:
            self.assertEqual(self.log(day, weight).status_code, 400, (day, weight))
        self.assertEqual(self.entries(), [])

    def test_edit_entry(self):
        self.log("2026-10-01", "80")
        eid = self.entries()[0]["id"]
        self.post(f"/body-weight/{eid}", {"entry_date": "2026-10-02", "weight": "79"})
        e = self.entries()[0]
        self.assertEqual((e["entry_date"].isoformat(), e["weight_kg"]), ("2026-10-02", 79))

    def test_edit_cannot_clash_with_other_date(self):
        self.log("2026-10-01", "80")
        self.log("2026-10-02", "79")
        first = self.entries()[0]["id"]
        self.post(f"/body-weight/{first}", {"entry_date": "2026-10-02", "weight": "78"})
        self.assertEqual([e["weight_kg"] for e in self.entries()], [80, 79])

    def test_delete_entry_with_confirmation(self):
        self.log("2026-10-01", "80")
        eid = self.entries()[0]["id"]
        self.assertIn(b"Delete entry", self.client.get(f"/body-weight/{eid}/delete").data)
        self.post(f"/body-weight/{eid}/delete")
        self.assertEqual(self.entries(), [])

    def test_pounds(self):
        self.post("/profile/", {"unit_system": "imperial", "age": "25", "weight": "176",
                                "height": "70", "fitness_level": "Beginner", "goal": "Lose weight"})
        self.log("2026-10-01", "176")
        self.assertAlmostEqual(self.entries()[0]["weight_kg"], 79.83, places=1)
        self.assertIn("176", self.client.get("/body-weight").data.decode())

    def test_entries_private(self):
        self.log("2026-10-01", "80")
        eid = self.entries()[0]["id"]
        self.logout()
        self.register(email="bob@example.com")
        self.assertEqual(self.post(f"/body-weight/{eid}/delete").status_code, 404)
        self.assertNotIn(b"80", self.client.get("/body-weight").data.split(b"<h2")[-1])
