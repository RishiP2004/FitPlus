"""PB-17 start, PB-18 log sets, PB-19 finish, PB-20 survive refresh,
PB-23 edit sets, PB-24 delete sessions, PB-25 notes."""
from datetime import timedelta

from app.db import execute, query_all
from tests.sprint2 import Sprint2Case


class StartWorkoutTests(Sprint2Case):  # PB-17
    def test_start_blank(self):
        sid = self.start()
        row = self.session(sid)
        self.assertIsNone(row["finished_at"])
        self.assertIsNone(row["template_id"])
        self.assertEqual(self.items(sid), [])
        self.assertIn(b"No exercises in this workout yet", self.client.get(f"/workouts/{sid}").data)

    def test_start_from_template_preloads_exercises(self):
        tid = self.make_template(exercises=(("Barbell Bench Press", 4, 6), ("Push-Up", 2, 15)))
        sid = self.start(tid)
        items = self.items(sid)
        self.assertEqual([(i["target_sets"], i["target_reps"]) for i in items], [(4, 6), (2, 15)])
        page = self.client.get(f"/workouts/{sid}").data.decode()
        self.assertIn("Push day", page)
        self.assertIn("target 4 × 6", page)
        self.assertLess(page.index("Barbell Bench Press"), page.index("Push-Up"))

    def test_start_page_lists_templates(self):
        self.make_template("Leg day", exercises=())
        page = self.client.get("/workouts/start").data
        self.assertIn(b"Start blank workout", page)
        self.assertIn(b"Leg day", page)

    def test_cannot_start_from_other_users_template(self):
        tid = self.make_template()
        self.logout()
        self.register(email="bob@example.com")
        self.assertEqual(self.post("/workouts/start", {"template_id": tid}).status_code, 404)


class LogSetsTests(Sprint2Case):  # PB-18
    def test_add_sets_listed_under_exercise(self):
        sid = self.start()
        squat = self.add_exercise(sid, "Barbell Back Squat")
        self.add_set(sid, squat, 8, 80)
        self.add_set(sid, squat, 6, 90)
        sets = self.sets(squat)
        self.assertEqual([(s["set_number"], s["reps"], s["weight_kg"]) for s in sets],
                         [(1, 8, 80), (2, 6, 90)])
        page = self.client.get(f"/workouts/{sid}").data.decode()
        block = page.split(f'id="ex-{squat}"')[1].split("</section>")[0]
        self.assertIn("<td>90</td>", block)

    def test_invalid_set_rejected(self):
        sid = self.start()
        item = self.add_exercise(sid, "Deadlift")
        for reps, weight in [(0, 50), ("x", 50), (5, -1), (5, "abc")]:
            self.add_set(sid, item, reps, weight)
        self.assertEqual(self.sets(item), [])

    def test_bodyweight_set_with_zero_weight(self):
        sid = self.start()
        item = self.add_exercise(sid, "Pull-Up")
        self.add_set(sid, item, 10, 0)
        self.assertEqual(self.sets(item)[0]["weight_kg"], 0)

    def test_pounds_converted_to_kg(self):
        self.post("/profile/", {"unit_system": "imperial", "age": "25", "weight": "160",
                                "height": "70", "fitness_level": "Beginner", "goal": "Get stronger"})
        sid = self.start()
        item = self.add_exercise(sid, "Deadlift")
        self.add_set(sid, item, 5, 225)
        self.assertAlmostEqual(self.sets(item)[0]["weight_kg"], 102.06, places=1)
        self.assertIn("<td>225</td>", self.client.get(f"/workouts/{sid}").data.decode())

    def test_delete_set_renumbers(self):
        sid = self.start()
        item = self.add_exercise(sid, "Deadlift")
        for w in (60, 70, 80):
            self.add_set(sid, item, 5, w)
        middle = self.sets(item)[1]["id"]
        self.post(f"/workouts/{sid}/sets/{middle}/delete")
        self.assertEqual([(s["set_number"], s["weight_kg"]) for s in self.sets(item)],
                         [(1, 60), (2, 80)])


class FinishWorkoutTests(Sprint2Case):  # PB-19
    def test_finish_saves_date_and_duration(self):
        sid = self.start()
        item = self.add_exercise(sid, "Deadlift")
        self.add_set(sid, item)
        # pretend the workout started 45 minutes ago
        row = self.session(sid)
        execute("UPDATE workout_sessions SET started_at = ? WHERE id = ?",
                (row["started_at"] - timedelta(minutes=45), sid))
        self.post(f"/workouts/{sid}/finish")
        row = self.session(sid)
        self.assertIsNotNone(row["finished_at"])
        self.assertAlmostEqual(row["duration_seconds"], 45 * 60, delta=5)
        self.assertIn(b"45 min", self.client.get(f"/workouts/{sid}").data)
        history = self.client.get("/history").data
        self.assertIn(b"1 workout", history)
        self.assertIn(f"/workouts/{sid}".encode(), history)

    def test_cannot_finish_empty_workout(self):
        sid = self.start()
        self.post(f"/workouts/{sid}/finish")
        self.assertIsNone(self.session(sid)["finished_at"])

    def test_only_one_active_workout(self):
        first = self.start()
        r = self.post("/workouts/start")
        self.assertIn(f"/workouts/{first}", r.headers["Location"])
        self.assertEqual(len(query_all("SELECT id FROM workout_sessions")), 1)


class SurviveRefreshTests(Sprint2Case):  # PB-20
    def test_sets_saved_immediately_and_survive_reload(self):
        sid = self.start()
        item = self.add_exercise(sid, "Deadlift")
        self.add_set(sid, item, 5, 120)
        page = self.client.get(f"/workouts/{sid}").data.decode()  # "refresh"
        self.assertIn("<td>120</td>", page)
        self.assertIn("In progress", page)

    def test_reopening_app_returns_to_unfinished_workout(self):
        sid = self.start()
        r = self.client.get("/")
        self.assertIn(f"/workouts/{sid}", r.headers["Location"])
        self.assertIn(b"Resume workout", self.client.get("/dashboard").data)

    def test_logging_back_in_returns_to_unfinished_workout(self):
        sid = self.start()
        self.logout()
        r = self.login()
        self.assertIn(f"/workouts/{sid}", r.headers["Location"])

    def test_start_page_redirects_to_unfinished_workout(self):
        sid = self.start()
        r = self.client.get("/workouts/start")
        self.assertIn(f"/workouts/{sid}", r.headers["Location"])


class EditPastSetsTests(Sprint2Case):  # PB-23
    def test_edit_logged_set_in_finished_session(self):
        sid, item = self.finished_workout(weight=100)
        set_id = self.sets(item)[0]["id"]
        page = self.client.get(f"/workouts/{sid}?edit={set_id}").data.decode()
        self.assertIn(f"/workouts/{sid}/sets/{set_id}", page)
        self.post(f"/workouts/{sid}/sets/{set_id}", {"reps": 6, "weight": 105})
        s = self.sets(item)[0]
        self.assertEqual((s["reps"], s["weight_kg"]), (6, 105))

    def test_invalid_edit_rejected(self):
        sid, item = self.finished_workout(weight=100)
        set_id = self.sets(item)[0]["id"]
        self.post(f"/workouts/{sid}/sets/{set_id}", {"reps": 0, "weight": 105})
        self.assertEqual(self.sets(item)[0]["reps"], 5)

    def test_cannot_edit_other_users_set(self):
        sid, item = self.finished_workout()
        set_id = self.sets(item)[0]["id"]
        self.logout()
        self.register(email="bob@example.com")
        r = self.post(f"/workouts/{sid}/sets/{set_id}", {"reps": 1, "weight": 1})
        self.assertEqual(r.status_code, 404)


class DeleteSessionTests(Sprint2Case):  # PB-24
    def test_delete_asks_for_confirmation(self):
        sid, _ = self.finished_workout()
        page = self.client.get(f"/workouts/{sid}/delete")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"cannot be undone", page.data)
        self.assertIsNotNone(self.session(sid))

    def test_deleted_session_removed_from_history(self):
        sid, _ = self.finished_workout()
        self.post(f"/workouts/{sid}/delete")
        self.assertIsNone(self.session(sid))
        self.assertIn(b"0 workouts", self.client.get("/history").data)
        self.assertEqual(query_all("SELECT id FROM session_sets"), [])

    def test_discard_active_workout(self):
        sid = self.start()
        self.assertIn(b"Discard workout", self.client.get(f"/workouts/{sid}/delete").data)
        self.post(f"/workouts/{sid}/delete")
        self.assertIsNone(self.session(sid))


class NotesTests(Sprint2Case):  # PB-25
    def test_notes_saved_and_shown(self):
        sid, _ = self.finished_workout()
        self.post(f"/workouts/{sid}/notes", {"notes": "Felt strong, PR on deadlift"})
        self.assertEqual(self.session(sid)["notes"], "Felt strong, PR on deadlift")
        self.assertIn(b"Felt strong, PR on deadlift", self.client.get(f"/workouts/{sid}").data)

    def test_notes_limited_to_500_chars(self):
        sid, _ = self.finished_workout()
        self.post(f"/workouts/{sid}/notes", {"notes": "a" * 500})
        self.assertEqual(len(self.session(sid)["notes"]), 500)
        self.post(f"/workouts/{sid}/notes", {"notes": "b" * 501})
        self.assertEqual(self.session(sid)["notes"], "a" * 500)
