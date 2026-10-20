"""Workout sessions (PB-17 to PB-20, PB-23 to PB-25).

A session is saved to the database the moment it starts, and every set is saved as
soon as it is added. An unfinished session (finished_at IS NULL) therefore survives
a page refresh, a closed tab or a logout, and the app sends the user back to it.
"""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .db import execute, query_all, query_one
from .exercises import group_by_muscle, search_exercises
from .routines import template_exercises, user_templates
from .security import login_required
from .util import fmt_weight, parse_float, parse_int, to_kg, utcnow, weight_unit

bp = Blueprint("workouts", __name__, url_prefix="/workouts")

NOTES_MAX = 500
REPS_RANGE = (1, 1000)
WEIGHT_RANGE = {"kg": (0, 1000), "lb": (0, 2200)}


# ------------------------------------------------------------------ data

def active_session(user_id):
    return query_one(
        "SELECT id, name, started_at FROM workout_sessions "
        "WHERE user_id = ? AND finished_at IS NULL ORDER BY started_at DESC, id DESC",
        (user_id,),
    )


def load_active_workout():
    """before_request hook: lets every page show a 'workout in progress' banner."""
    g.active_workout = active_session(g.user["id"]) if g.get("user") else None


def get_session(session_id, user_id):
    row = query_one("SELECT * FROM workout_sessions WHERE id = ? AND user_id = ?",
                    (session_id, user_id))
    if row is None:
        abort(404)
    return row


def _get_session_exercise(session_id, item_id):
    row = query_one("SELECT * FROM session_exercises WHERE id = ? AND session_id = ?",
                    (item_id, session_id))
    if row is None:
        abort(404)
    return row


def _get_set(session_id, set_id):
    row = query_one(
        "SELECT ss.* FROM session_sets ss JOIN session_exercises se ON se.id = ss.session_exercise_id "
        "WHERE ss.id = ? AND se.session_id = ?",
        (set_id, session_id),
    )
    if row is None:
        abort(404)
    return row


def session_detail(session_id, unit):
    """Exercises of a session, each with its sets, in display units."""
    exercises = query_all(
        "SELECT se.id, se.exercise_id, se.position, se.target_sets, se.target_reps, "
        "e.name, e.muscle_group, e.equipment "
        "FROM session_exercises se JOIN exercises e ON e.id = se.exercise_id "
        "WHERE se.session_id = ? ORDER BY se.position, se.id",
        (session_id,),
    )
    sets = query_all(
        "SELECT ss.id, ss.session_exercise_id, ss.set_number, ss.reps, ss.weight_kg "
        "FROM session_sets ss JOIN session_exercises se ON se.id = ss.session_exercise_id "
        "WHERE se.session_id = ? ORDER BY ss.set_number, ss.id",
        (session_id,),
    )
    by_item = {}
    for s in sets:
        s["weight"] = fmt_weight(s["weight_kg"], unit)
        by_item.setdefault(s["session_exercise_id"], []).append(s)
    for ex in exercises:
        ex["sets"] = by_item.get(ex["id"], [])
    total_sets = len(sets)
    volume = sum(s["reps"] * s["weight_kg"] for s in sets)
    return exercises, total_sets, fmt_weight(volume, unit)


def _renumber_sets(item_id):
    rows = query_all("SELECT id, set_number FROM session_sets WHERE session_exercise_id = ? "
                     "ORDER BY set_number, id", (item_id,))
    for i, row in enumerate(rows, start=1):
        if row["set_number"] != i:
            execute("UPDATE session_sets SET set_number = ? WHERE id = ?", (i, row["id"]))


def _parse_set(form, unit):
    reps = parse_int(form.get("reps"), *REPS_RANGE)
    weight = parse_float(form.get("weight"), *WEIGHT_RANGE[unit])
    if reps is None:
        return None, f"Reps must be a whole number from {REPS_RANGE[0]} to {REPS_RANGE[1]}."
    if weight is None:
        low, high = WEIGHT_RANGE[unit]
        return None, f"Weight must be a number from {low} to {high} {unit} (0 for bodyweight)."
    return (reps, round(to_kg(weight, unit), 3)), None


def _back(session_id, anchor=""):
    return redirect(url_for("workouts.view", session_id=session_id) + anchor)


# ------------------------------------------------------------------ start

@bp.route("/start", methods=("GET", "POST"))
@login_required
def start():
    active = active_session(g.user["id"])
    if active:
        if request.method == "POST":
            flash("You already have a workout in progress. Finish or discard it first.", "error")
        return redirect(url_for("workouts.view", session_id=active["id"]))
    if request.method == "GET":
        return render_template("workouts/start.html", templates=user_templates(g.user["id"]))

    template = None
    template_id = request.form.get("template_id")
    if template_id:
        template = query_one("SELECT * FROM workout_templates WHERE id = ? AND user_id = ?",
                             (parse_int(template_id, 1, 10**9), g.user["id"]))
        if template is None:
            abort(404)
    name = template["name"] if template else "Workout"
    session = execute(
        "INSERT INTO workout_sessions (user_id, template_id, name, started_at) "
        "VALUES (?, ?, ?, ?) RETURNING id",
        (g.user["id"], template["id"] if template else None, name, utcnow()),
    )
    if template:
        for item in template_exercises(template["id"]):
            execute(
                "INSERT INTO session_exercises (session_id, exercise_id, position, target_sets, "
                "target_reps) VALUES (?, ?, ?, ?, ?)",
                (session["id"], item["exercise_id"], item["position"], item["target_sets"],
                 item["target_reps"]),
            )
    return redirect(url_for("workouts.view", session_id=session["id"]))


# ------------------------------------------------------------------ view

@bp.route("/<int:session_id>")
@login_required
def view(session_id):
    session = get_session(session_id, g.user["id"])
    unit = weight_unit(g.user["id"])
    exercises, total_sets, volume = session_detail(session_id, unit)
    return render_template(
        "workouts/session.html", session=session, exercises=exercises, total_sets=total_sets,
        volume=volume, unit=unit, active=session["finished_at"] is None,
        library=group_by_muscle(search_exercises()), notes_max=NOTES_MAX,
        edit_set=parse_int(request.args.get("edit"), 1, 10**12),
    )


# ------------------------------------------------------------------ exercises

@bp.route("/<int:session_id>/exercises", methods=("POST",))
@login_required
def add_exercise(session_id):
    get_session(session_id, g.user["id"])
    exercise_id = parse_int(request.form.get("exercise_id"), 1, 10**9)
    exercise = exercise_id and query_one(
        "SELECT id, name FROM exercises WHERE id = ? AND created_by IS NULL", (exercise_id,))
    if not exercise:
        flash("Choose an exercise from the library.", "error")
        return _back(session_id)
    last = query_one("SELECT MAX(position) AS p FROM session_exercises WHERE session_id = ?",
                     (session_id,))["p"] or 0
    row = execute("INSERT INTO session_exercises (session_id, exercise_id, position) "
                  "VALUES (?, ?, ?) RETURNING id", (session_id, exercise["id"], last + 1))
    return _back(session_id, f"#ex-{row['id']}")


@bp.route("/<int:session_id>/exercises/<int:item_id>/remove", methods=("POST",))
@login_required
def remove_exercise(session_id, item_id):
    get_session(session_id, g.user["id"])
    item = _get_session_exercise(session_id, item_id)
    execute("DELETE FROM session_exercises WHERE id = ?", (item["id"],))
    flash("Exercise removed from this workout.", "success")
    return _back(session_id)


# ------------------------------------------------------------------ sets

@bp.route("/<int:session_id>/exercises/<int:item_id>/sets", methods=("POST",))
@login_required
def add_set(session_id, item_id):
    get_session(session_id, g.user["id"])
    item = _get_session_exercise(session_id, item_id)
    values, error = _parse_set(request.form, weight_unit(g.user["id"]))
    if error:
        flash(error, "error")
        return _back(session_id, f"#ex-{item_id}")
    count = query_one("SELECT COUNT(*) AS n FROM session_sets WHERE session_exercise_id = ?",
                      (item["id"],))["n"]
    execute("INSERT INTO session_sets (session_exercise_id, set_number, reps, weight_kg) "
            "VALUES (?, ?, ?, ?)", (item["id"], count + 1, *values))
    return _back(session_id, f"#ex-{item_id}")


@bp.route("/<int:session_id>/sets/<int:set_id>", methods=("POST",))
@login_required
def update_set(session_id, set_id):
    get_session(session_id, g.user["id"])
    row = _get_set(session_id, set_id)
    values, error = _parse_set(request.form, weight_unit(g.user["id"]))
    if error:
        flash(error, "error")
        return redirect(url_for("workouts.view", session_id=session_id, edit=set_id)
                        + f"#ex-{row['session_exercise_id']}")
    execute("UPDATE session_sets SET reps = ?, weight_kg = ? WHERE id = ?", (*values, set_id))
    flash("Set updated.", "success")
    return _back(session_id, f"#ex-{row['session_exercise_id']}")


@bp.route("/<int:session_id>/sets/<int:set_id>/delete", methods=("POST",))
@login_required
def delete_set(session_id, set_id):
    get_session(session_id, g.user["id"])
    row = _get_set(session_id, set_id)
    execute("DELETE FROM session_sets WHERE id = ?", (set_id,))
    _renumber_sets(row["session_exercise_id"])
    return _back(session_id, f"#ex-{row['session_exercise_id']}")


# ------------------------------------------------------------------ finish / notes / delete

@bp.route("/<int:session_id>/finish", methods=("POST",))
@login_required
def finish(session_id):
    session = get_session(session_id, g.user["id"])
    if session["finished_at"] is not None:
        return _back(session_id)
    sets = query_one(
        "SELECT COUNT(*) AS n FROM session_sets ss JOIN session_exercises se "
        "ON se.id = ss.session_exercise_id WHERE se.session_id = ?", (session_id,))["n"]
    if not sets:
        flash("Log at least one set before finishing, or discard this workout.", "error")
        return _back(session_id)
    now = utcnow()
    duration = max(0, int((now - session["started_at"]).total_seconds()))
    execute("UPDATE workout_sessions SET finished_at = ?, duration_seconds = ? WHERE id = ?",
            (now, duration, session_id))
    flash("Workout saved to your history.", "success")
    return _back(session_id)


@bp.route("/<int:session_id>/notes", methods=("POST",))
@login_required
def save_notes(session_id):
    get_session(session_id, g.user["id"])
    notes = (request.form.get("notes") or "").strip()
    if len(notes) > NOTES_MAX:
        flash(f"Notes can be at most {NOTES_MAX} characters (you entered {len(notes)}).", "error")
        return _back(session_id, "#notes")
    execute("UPDATE workout_sessions SET notes = ? WHERE id = ?", (notes or None, session_id))
    flash("Notes saved.", "success")
    return _back(session_id, "#notes")


@bp.route("/<int:session_id>/delete", methods=("GET", "POST"))
@login_required
def delete(session_id):
    session = get_session(session_id, g.user["id"])
    active = session["finished_at"] is None
    if request.method == "POST":
        execute("DELETE FROM workout_sessions WHERE id = ?", (session_id,))
        flash("Workout discarded." if active else "Workout deleted from your history.", "success")
        return redirect(url_for("workouts.start" if active else "history.index"))
    if active:
        message = "Discard this workout? The sets you logged in it will be lost."
        button = "Discard workout"
    else:
        message = "Delete this workout from your history? This cannot be undone."
        button = "Delete workout"
    return render_template("confirm.html", title=button, message=message, button=button,
                           action=url_for("workouts.delete", session_id=session_id),
                           cancel=url_for("workouts.view", session_id=session_id))
