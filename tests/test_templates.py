"""PB-14 create/name template, PB-15 build/reorder/remove, PB-16 edit/delete."""
from app.db import query_all, query_one
from tests.sprint2 import Sprint2Case


class CreateTemplateTests(Sprint2Case):  # PB-14
    def test_create_named_template_saved_to_account(self):
        tid = self.make_template("Push day", exercises=())
        row = query_one("SELECT * FROM workout_templates WHERE id = ?", (tid,))
        self.assertEqual(row["name"], "Push day")
        self.assertEqual(row["user_id"], self.uid)
        self.assertIn(b"Push day", self.client.get("/templates/").data)

    def test_name_required_and_limited(self):
        self.assertEqual(self.post("/templates/new", {"name": "   "}).status_code, 400)
        self.assertEqual(self.post("/templates/new", {"name": "x" * 61}).status_code, 400)
        self.assertEqual(query_all("SELECT id FROM workout_templates"), [])

    def test_templates_private_to_owner(self):
        tid = self.make_template()
        self.logout()
        self.register(email="bob@example.com")
        self.assertEqual(self.client.get(f"/templates/{tid}").status_code, 404)
        self.assertIn(b"No templates yet", self.client.get("/templates/").data)

    def test_requires_login(self):
        self.logout()
        self.assertEqual(self.client.get("/templates/").status_code, 302)


class BuildTemplateTests(Sprint2Case):  # PB-15
    def setUp(self):
        super().setUp()
        self.tid = self.make_template(exercises=(
            ("Barbell Bench Press", 4, 6), ("Overhead Press", 3, 8), ("Push-Up", 2, 15)))

    def names(self):
        return [r["name"] for r in query_all(
            "SELECT e.name FROM template_exercises te JOIN exercises e ON e.id = te.exercise_id "
            "WHERE te.template_id = ? ORDER BY te.position", (self.tid,))]

    def item(self, name):
        return query_one("SELECT te.* FROM template_exercises te JOIN exercises e ON "
                         "e.id = te.exercise_id WHERE te.template_id = ? AND e.name = ?",
                         (self.tid, name))

    def test_add_from_library_with_targets(self):
        self.assertEqual(self.names(), ["Barbell Bench Press", "Overhead Press", "Push-Up"])
        bench = self.item("Barbell Bench Press")
        self.assertEqual((bench["target_sets"], bench["target_reps"]), (4, 6))
        page = self.client.get(f"/templates/{self.tid}").data.decode()
        self.assertIn("Overhead Press", page)

    def test_invalid_targets_or_exercise_rejected(self):
        self.post(f"/templates/{self.tid}/exercises",
                  {"exercise_id": self.ex("Deadlift"), "target_sets": 0, "target_reps": 5})
        self.post(f"/templates/{self.tid}/exercises",
                  {"exercise_id": 99999, "target_sets": 3, "target_reps": 5})
        self.assertEqual(len(self.names()), 3)

    def test_update_targets(self):
        item = self.item("Push-Up")
        self.post(f"/templates/{self.tid}/exercises/{item['id']}",
                  {"target_sets": 3, "target_reps": 20})
        item = self.item("Push-Up")
        self.assertEqual((item["target_sets"], item["target_reps"]), (3, 20))

    def test_reorder(self):
        item = self.item("Push-Up")
        self.post(f"/templates/{self.tid}/exercises/{item['id']}/move", {"direction": "up"})
        self.assertEqual(self.names(), ["Barbell Bench Press", "Push-Up", "Overhead Press"])
        bench = self.item("Barbell Bench Press")
        self.post(f"/templates/{self.tid}/exercises/{bench['id']}/move", {"direction": "down"})
        self.assertEqual(self.names(), ["Push-Up", "Barbell Bench Press", "Overhead Press"])
        # moving the first item up does nothing
        first = self.item("Push-Up")
        self.post(f"/templates/{self.tid}/exercises/{first['id']}/move", {"direction": "up"})
        self.assertEqual(self.names()[0], "Push-Up")

    def test_remove(self):
        item = self.item("Overhead Press")
        self.post(f"/templates/{self.tid}/exercises/{item['id']}/remove")
        self.assertEqual(self.names(), ["Barbell Bench Press", "Push-Up"])
        positions = [r["position"] for r in query_all(
            "SELECT position FROM template_exercises WHERE template_id = ? ORDER BY position",
            (self.tid,))]
        self.assertEqual(positions, [1, 2])


class EditDeleteTemplateTests(Sprint2Case):  # PB-16
    def test_rename(self):
        tid = self.make_template("Push day")
        self.post(f"/templates/{tid}/rename", {"name": "Chest & shoulders"})
        self.assertEqual(query_one("SELECT name FROM workout_templates WHERE id = ?", (tid,))["name"],
                         "Chest & shoulders")

    def test_delete_asks_then_deletes(self):
        tid = self.make_template()
        page = self.client.get(f"/templates/{tid}/delete")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Delete template", page.data)
        self.assertIsNotNone(query_one("SELECT id FROM workout_templates WHERE id = ?", (tid,)))
        self.post(f"/templates/{tid}/delete")
        self.assertIsNone(query_one("SELECT id FROM workout_templates WHERE id = ?", (tid,)))
        self.assertEqual(query_all("SELECT id FROM template_exercises"), [])

    def test_deleting_template_keeps_past_workouts(self):
        tid = self.make_template()
        sid = self.start(tid)
        item = self.items(sid)[0]["id"]
        self.add_set(sid, item)
        self.post(f"/workouts/{sid}/finish")
        self.post(f"/templates/{tid}/delete")
        row = self.session(sid)
        self.assertIsNotNone(row)
        self.assertIsNone(row["template_id"])

    def test_cannot_delete_someone_elses_template(self):
        tid = self.make_template()
        self.logout()
        self.register(email="bob@example.com")
        self.assertEqual(self.post(f"/templates/{tid}/delete").status_code, 404)
