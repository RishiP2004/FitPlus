"""Exercise library: browse, detail, search and filter (PB-10 to PB-13)."""
from flask import Blueprint, abort, render_template, request

from .db import query_all, query_one
from .security import login_required

bp = Blueprint("exercises", __name__, url_prefix="/exercises")

# Display order for muscle groups; any new group sorts after these.
MUSCLE_ORDER = ["Chest", "Back", "Shoulders", "Biceps", "Triceps", "Quadriceps",
                "Hamstrings", "Glutes", "Calves", "Core", "Full Body"]


def _muscle_key(name):
    return (MUSCLE_ORDER.index(name) if name in MUSCLE_ORDER else len(MUSCLE_ORDER), name)


def search_exercises(q="", muscle="", equipment=""):
    sql = ("SELECT id, name, muscle_group, equipment FROM exercises "
           "WHERE created_by IS NULL")
    params = []
    if q:
        sql += " AND LOWER(name) LIKE ?"
        params.append(f"%{q.lower()}%")
    if muscle:
        sql += " AND muscle_group = ?"
        params.append(muscle)
    if equipment:
        sql += " AND equipment = ?"
        params.append(equipment)
    sql += " ORDER BY name"
    return query_all(sql, tuple(params))


def group_by_muscle(rows):
    groups = {}
    for row in rows:
        groups.setdefault(row["muscle_group"], []).append(row)
    return [(m, groups[m]) for m in sorted(groups, key=_muscle_key)]


@bp.route("/")
@login_required
def index():
    q = request.args.get("q", "").strip()[:100]
    muscle = request.args.get("muscle", "")
    equipment = request.args.get("equipment", "")
    muscles = sorted(
        (r["muscle_group"] for r in query_all(
            "SELECT DISTINCT muscle_group FROM exercises WHERE created_by IS NULL")),
        key=_muscle_key,
    )
    equipment_list = [r["equipment"] for r in query_all(
        "SELECT DISTINCT equipment FROM exercises WHERE created_by IS NULL ORDER BY equipment")]
    # Render the whole library and mark non-matches hidden, so live filtering
    # in the browser can reveal them again without another request.
    matches = {r["id"] for r in search_exercises(q, muscle, equipment)}
    rows = search_exercises()
    return render_template(
        "exercises/index.html", groups=group_by_muscle(rows), matches=matches,
        total=len(matches),
        q=q, muscle=muscle, equipment=equipment, muscles=muscles,
        equipment_list=equipment_list,
    )


@bp.route("/<int:exercise_id>")
@login_required
def detail(exercise_id):
    exercise = query_one(
        "SELECT id, name, muscle_group, equipment, instructions FROM exercises "
        "WHERE id = ? AND created_by IS NULL",
        (exercise_id,),
    )
    if exercise is None:
        abort(404)
    return render_template("exercises/detail.html", exercise=exercise)
