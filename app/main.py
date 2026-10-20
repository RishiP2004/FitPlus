"""Starter/home page, health check and dashboard (PB-03, PB-06, PB-20)."""
from flask import Blueprint, g, jsonify, redirect, render_template, url_for

from .db import query_one
from .profile import get_profile, to_display
from .security import login_required

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if g.user:
        if g.active_workout:  # PB-20: reopening the app returns to the unfinished workout
            return redirect(url_for("workouts.view", session_id=g.active_workout["id"]))
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@bp.route("/health")
def health():
    try:
        count = query_one("SELECT COUNT(*) AS n FROM exercises")["n"]
        return jsonify(status="ok", database="ok", preset_exercises=count)
    except Exception as exc:  # report, don't crash, so the host can see it
        return jsonify(status="error", database="unreachable", detail=type(exc).__name__), 503


@bp.route("/dashboard")
@login_required
def dashboard():
    profile = get_profile(g.user["id"])
    shown = to_display(profile) if profile else None
    exercise_count = query_one(
        "SELECT COUNT(*) AS n FROM exercises WHERE created_by IS NULL"
    )["n"]
    uid = g.user["id"]
    stats = {
        "templates": query_one("SELECT COUNT(*) AS n FROM workout_templates WHERE user_id = ?",
                               (uid,))["n"],
        "workouts": query_one("SELECT COUNT(*) AS n FROM workout_sessions WHERE user_id = ? "
                              "AND finished_at IS NOT NULL", (uid,))["n"],
        "last": query_one("SELECT id, name, started_at FROM workout_sessions WHERE user_id = ? "
                          "AND finished_at IS NOT NULL ORDER BY started_at DESC, id DESC", (uid,)),
    }
    return render_template(
        "dashboard.html", profile=profile, shown=shown, exercise_count=exercise_count,
        stats=stats,
    )
