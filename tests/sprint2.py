"""Helpers shared by the Sprint 2 tests."""
import re

from app.db import query_all, query_one
from tests.base import AppTestCase


class Sprint2Case(AppTestCase):
    def setUp(self):
        super().setUp()
        self.register()
        self.uid = self.user()["id"]

    def ex(self, name):
        return query_one("SELECT id FROM exercises WHERE name = ?", (name,))["id"]

    def make_template(self, name="Push day", exercises=(("Barbell Bench Press", 3, 8),)):
        r = self.post("/templates/new", {"name": name})
        tid = int(re.search(r"/templates/(\d+)", r.headers["Location"]).group(1))
        for ex_name, sets, reps in exercises:
            self.post(f"/templates/{tid}/exercises",
                      {"exercise_id": self.ex(ex_name), "target_sets": sets, "target_reps": reps})
        return tid

    def start(self, template_id=None):
        data = {"template_id": template_id} if template_id else {}
        r = self.post("/workouts/start", data)
        return int(re.search(r"/workouts/(\d+)", r.headers["Location"]).group(1))

    def items(self, session_id):
        return query_all("SELECT * FROM session_exercises WHERE session_id = ? ORDER BY position",
                         (session_id,))

    def add_exercise(self, session_id, name):
        self.post(f"/workouts/{session_id}/exercises", {"exercise_id": self.ex(name)})
        return self.items(session_id)[-1]["id"]

    def add_set(self, session_id, item_id, reps=10, weight=60):
        return self.post(f"/workouts/{session_id}/exercises/{item_id}/sets",
                         {"reps": reps, "weight": weight})

    def sets(self, item_id):
        return query_all("SELECT * FROM session_sets WHERE session_exercise_id = ? "
                         "ORDER BY set_number", (item_id,))

    def finished_workout(self, name_ex="Deadlift", reps=5, weight=100):
        sid = self.start()
        item = self.add_exercise(sid, name_ex)
        self.add_set(sid, item, reps, weight)
        self.post(f"/workouts/{sid}/finish")
        return sid, item

    def session(self, sid):
        return query_one("SELECT * FROM workout_sessions WHERE id = ?", (sid,))
