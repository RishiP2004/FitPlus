"""Workout templates (PB-14 to PB-16): create, name, build, reorder, edit and delete."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .db import execute, query_all, query_one
from .exercises import group_by_muscle, search_exercises
from .security import login_required
from .util import parse_int, utcnow

bp = Blueprint("routines", __name__, url_prefix="/templates")

NAME_MAX = 60
SETS_RANGE = (1, 20)
REPS_RANGE = (1, 100)


def get_template(template_id, user_id):
    """The user's template, or 404 (also for other users' templates)."""
    row = query_one(
        "SELECT * FROM workout_templates WHERE id = ? AND user_id = ?", (template_id, user_id)
    )
    if row is None:
        abort(404)
    return row


def template_exercises(template_id):
    return query_all(
        "SELECT te.id, te.exercise_id, te.position, te.target_sets, te.target_reps, "
        "e.name, e.muscle_group, e.equipment "
        "FROM template_exercises te JOIN exercises e ON e.id = te.exercise_id "
        "WHERE te.template_id = ? ORDER BY te.position, te.id",
        (template_id,),
    )


def user_templates(user_id):
    return query_all(
        "SELECT t.id, t.name, t.updated_at, "
        "(SELECT COUNT(*) FROM template_exercises te WHERE te.template_id = t.id) AS exercise_count "
        "FROM workout_templates t WHERE t.user_id = ? ORDER BY LOWER(t.name), t.id",
        (user_id,),
    )


def validate_name(raw):
    name = " ".join((raw or "").split())
    if not name:
        return None, "Give the template a name."
    if len(name) > NAME_MAX:
        return None, f"Keep the name to {NAME_MAX} characters or fewer."
    return name, None


def _touch(template_id):
    execute("UPDATE workout_templates SET updated_at = ? WHERE id = ?", (utcnow(), template_id))


def _renumber(template_id):
    """Make positions 1..n with no gaps (after a removal)."""
    for i, row in enumerate(template_exercises(template_id), start=1):
        if row["position"] != i:
            execute("UPDATE template_exercises SET position = ? WHERE id = ?", (i, row["id"]))


def _get_item(template_id, item_id):
    row = query_one(
        "SELECT * FROM template_exercises WHERE id = ? AND template_id = ?", (item_id, template_id)
    )
    if row is None:
        abort(404)
    return row


# ------------------------------------------------------------------ views

@bp.route("/")
@login_required
def index():
    return render_template("routines/index.html", templates=user_templates(g.user["id"]),
                           errors={}, name="")


@bp.route("/new", methods=("POST",))
@login_required
def create():
    name, error = validate_name(request.form.get("name"))
    if error:
        return render_template("routines/index.html", templates=user_templates(g.user["id"]),
                               errors={"name": error}, name=request.form.get("name", "")), 400
    now = utcnow()
    row = execute(
        "INSERT INTO workout_templates (user_id, name, created_at, updated_at) "
        "VALUES (?, ?, ?, ?) RETURNING id",
        (g.user["id"], name, now, now),
    )
    flash(f"Template “{name}” created. Now add some exercises.", "success")
    return redirect(url_for("routines.edit", template_id=row["id"]))


@bp.route("/<int:template_id>")
@login_required
def edit(template_id):
    template = get_template(template_id, g.user["id"])
    return render_template(
        "routines/edit.html", template=template, items=template_exercises(template_id),
        library=group_by_muscle(search_exercises()), errors={},
    )


@bp.route("/<int:template_id>/rename", methods=("POST",))
@login_required
def rename(template_id):
    template = get_template(template_id, g.user["id"])
    name, error = validate_name(request.form.get("name"))
    if error:
        flash(error, "error")
    else:
        execute("UPDATE workout_templates SET name = ?, updated_at = ? WHERE id = ?",
                (name, utcnow(), template["id"]))
        flash("Template renamed.", "success")
    return redirect(url_for("routines.edit", template_id=template_id))


@bp.route("/<int:template_id>/exercises", methods=("POST",))
@login_required
def add_exercise(template_id):
    get_template(template_id, g.user["id"])
    exercise_id = parse_int(request.form.get("exercise_id"), 1, 10**9)
    sets = parse_int(request.form.get("target_sets"), *SETS_RANGE)
    reps = parse_int(request.form.get("target_reps"), *REPS_RANGE)
    exercise = exercise_id and query_one(
        "SELECT id, name FROM exercises WHERE id = ? AND created_by IS NULL", (exercise_id,))
    if not exercise:
        flash("Choose an exercise from the library.", "error")
    elif sets is None or reps is None:
        flash(f"Target sets must be {SETS_RANGE[0]}–{SETS_RANGE[1]} and reps "
              f"{REPS_RANGE[0]}–{REPS_RANGE[1]}.", "error")
    else:
        last = query_one("SELECT MAX(position) AS p FROM template_exercises WHERE template_id = ?",
                         (template_id,))["p"] or 0
        execute(
            "INSERT INTO template_exercises (template_id, exercise_id, position, target_sets, "
            "target_reps) VALUES (?, ?, ?, ?, ?)",
            (template_id, exercise["id"], last + 1, sets, reps),
        )
        _touch(template_id)
        flash(f"Added {exercise['name']}.", "success")
    return redirect(url_for("routines.edit", template_id=template_id))


@bp.route("/<int:template_id>/exercises/<int:item_id>", methods=("POST",))
@login_required
def update_exercise(template_id, item_id):
    get_template(template_id, g.user["id"])
    item = _get_item(template_id, item_id)
    sets = parse_int(request.form.get("target_sets"), *SETS_RANGE)
    reps = parse_int(request.form.get("target_reps"), *REPS_RANGE)
    if sets is None or reps is None:
        flash(f"Target sets must be {SETS_RANGE[0]}–{SETS_RANGE[1]} and reps "
              f"{REPS_RANGE[0]}–{REPS_RANGE[1]}.", "error")
    else:
        execute("UPDATE template_exercises SET target_sets = ?, target_reps = ? WHERE id = ?",
                (sets, reps, item["id"]))
        _touch(template_id)
        flash("Targets updated.", "success")
    return redirect(url_for("routines.edit", template_id=template_id))


@bp.route("/<int:template_id>/exercises/<int:item_id>/move", methods=("POST",))
@login_required
def move_exercise(template_id, item_id):
    get_template(template_id, g.user["id"])
    _get_item(template_id, item_id)
    items = template_exercises(template_id)
    ids = [r["id"] for r in items]
    i = ids.index(item_id)
    j = i - 1 if request.form.get("direction") == "up" else i + 1
    if 0 <= j < len(items):
        a, b = items[i], items[j]
        execute("UPDATE template_exercises SET position = ? WHERE id = ?", (b["position"], a["id"]))
        execute("UPDATE template_exercises SET position = ? WHERE id = ?", (a["position"], b["id"]))
        if a["position"] == b["position"]:
            _renumber(template_id)
        _touch(template_id)
    return redirect(url_for("routines.edit", template_id=template_id) + f"#item-{item_id}")


@bp.route("/<int:template_id>/exercises/<int:item_id>/remove", methods=("POST",))
@login_required
def remove_exercise(template_id, item_id):
    get_template(template_id, g.user["id"])
    item = _get_item(template_id, item_id)
    execute("DELETE FROM template_exercises WHERE id = ?", (item["id"],))
    _renumber(template_id)
    _touch(template_id)
    flash("Exercise removed from the template.", "success")
    return redirect(url_for("routines.edit", template_id=template_id))


@bp.route("/<int:template_id>/delete", methods=("GET", "POST"))
@login_required
def delete(template_id):
    template = get_template(template_id, g.user["id"])
    if request.method == "POST":
        execute("DELETE FROM workout_templates WHERE id = ?", (template["id"],))
        flash(f"Template “{template['name']}” deleted.", "success")
        return redirect(url_for("routines.index"))
    return render_template(
        "confirm.html", title="Delete template",
        message=f"Delete the template “{template['name']}”? Past workouts started from it are kept.",
        action=url_for("routines.delete", template_id=template_id), button="Delete template",
        cancel=url_for("routines.edit", template_id=template_id),
    )
