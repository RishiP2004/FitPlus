"""Fitness profile (PB-08). Values are stored in metric (kg, cm) and converted for display."""
from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .db import execute, query_one
from .security import login_required

bp = Blueprint("profile", __name__, url_prefix="/profile")

KG_PER_LB = 0.45359237
CM_PER_IN = 2.54

FITNESS_LEVELS = ["Beginner", "Intermediate", "Advanced"]
GOALS = ["Lose weight", "Build muscle", "Get stronger", "Improve endurance", "Stay healthy"]
UNIT_SYSTEMS = {"metric": ("kg", "cm"), "imperial": ("lb", "in")}

# Accepted ranges, in the units the user typed.
LIMITS = {
    "age": (13, 100),
    "metric": {"weight": (25, 300), "height": (100, 250)},
    "imperial": {"weight": (55, 660), "height": (39, 98)},
}


def get_profile(user_id):
    return query_one("SELECT * FROM profiles WHERE user_id = ?", (user_id,))


def to_display(profile):
    """Profile values in the user's chosen units, rounded for forms and display."""
    units = profile.get("unit_system") or "metric"
    w, h = profile.get("weight_kg"), profile.get("height_cm")
    if units == "imperial":
        w = w / KG_PER_LB if w is not None else None
        h = h / CM_PER_IN if h is not None else None
    return {
        "age": profile.get("age"),
        "weight": round(w, 1) if w is not None else None,
        "height": round(h, 1) if h is not None else None,
        "fitness_level": profile.get("fitness_level"),
        "goal": profile.get("goal"),
        "unit_system": units,
        "weight_unit": UNIT_SYSTEMS[units][0],
        "height_unit": UNIT_SYSTEMS[units][1],
    }


def _number(raw, field, low, high, errors, as_int=False):
    raw = (raw or "").strip()
    if not raw:
        errors[field] = "This field is required."
        return None
    try:
        value = int(raw) if as_int else float(raw)
    except ValueError:
        errors[field] = "Enter a number."
        return None
    if not (low <= value <= high):
        errors[field] = f"Enter a value between {low} and {high}."
        return None
    return value


def validate_profile(form):
    errors = {}
    units = form.get("unit_system", "metric")
    if units not in UNIT_SYSTEMS:
        errors["unit_system"] = "Choose kg or lb."
        units = "metric"
    age = _number(form.get("age"), "age", *LIMITS["age"], errors, as_int=True)
    weight = _number(form.get("weight"), "weight", *LIMITS[units]["weight"], errors)
    height = _number(form.get("height"), "height", *LIMITS[units]["height"], errors)
    level = form.get("fitness_level", "")
    if level not in FITNESS_LEVELS:
        errors["fitness_level"] = "Choose a fitness level."
    goal = form.get("goal", "")
    if goal not in GOALS:
        errors["goal"] = "Choose a goal."
    if errors:
        return None, errors
    if units == "imperial":
        weight *= KG_PER_LB
        height *= CM_PER_IN
    return {
        "age": age,
        "weight_kg": round(weight, 2),
        "height_cm": round(height, 2),
        "fitness_level": level,
        "goal": goal,
        "unit_system": units,
    }, {}


def save_profile(user_id, data):
    params = (data["age"], data["height_cm"], data["weight_kg"], data["fitness_level"],
              data["goal"], data["unit_system"])
    if get_profile(user_id):
        execute(
            "UPDATE profiles SET age = ?, height_cm = ?, weight_kg = ?, fitness_level = ?, "
            "goal = ?, unit_system = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            params + (user_id,),
        )
    else:
        execute(
            "INSERT INTO profiles (age, height_cm, weight_kg, fitness_level, goal, unit_system, "
            "user_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            params + (user_id,),
        )


@bp.route("/", methods=("GET", "POST"))
@login_required
def edit():
    profile = get_profile(g.user["id"])
    errors = {}
    if request.method == "POST":
        data, errors = validate_profile(request.form)
        if not errors:
            save_profile(g.user["id"], data)
            flash("Profile saved.", "success")
            return redirect(url_for("main.dashboard"))
        units = request.form.get("unit_system", "metric")
        units = units if units in UNIT_SYSTEMS else "metric"
        values = dict(request.form)
        values.update(weight_unit=UNIT_SYSTEMS[units][0], height_unit=UNIT_SYSTEMS[units][1],
                      unit_system=units)
        return render_template("profile.html", values=values, errors=errors,
                               levels=FITNESS_LEVELS, goals=GOALS, is_new=profile is None), 400
    values = to_display(profile) if profile else to_display({"unit_system": "metric"})
    return render_template("profile.html", values=values, errors=errors,
                           levels=FITNESS_LEVELS, goals=GOALS, is_new=profile is None,
                           welcome=request.args.get("welcome"))
