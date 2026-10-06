"""Starter/home page, health check and dashboard (PB-03, PB-06)."""
from flask import Blueprint, g, jsonify, redirect, render_template, url_for

from .db import query_one
from .profile import get_profile, to_display
from .security import login_required

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    if g.user:
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
    return render_template(
        "dashboard.html", profile=profile, shown=shown, exercise_count=exercise_count
    )
