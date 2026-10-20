"""Workout history (PB-21, PB-22) and body weight log (PB-26)."""
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for

from .db import execute, integrity_errors, query_all, query_one
from .security import login_required
from .util import (fmt_weight, local_day_bounds_utc, local_today, parse_date, parse_float,
                   to_kg, weight_unit)

bp = Blueprint("history", __name__)

BODY_WEIGHT_RANGE = {"kg": (20, 400), "lb": (44, 880)}


def finished_sessions(user_id, start_utc=None, end_utc=None):
    sql = (
        "SELECT s.id, s.name, s.started_at, s.duration_seconds, s.notes, "
        "(SELECT COUNT(*) FROM session_exercises se WHERE se.session_id = s.id) AS exercise_count, "
        "(SELECT COUNT(*) FROM session_sets ss JOIN session_exercises se "
        "   ON se.id = ss.session_exercise_id WHERE se.session_id = s.id) AS set_count, "
        "(SELECT COALESCE(SUM(ss.reps * ss.weight_kg), 0) FROM session_sets ss "
        "   JOIN session_exercises se ON se.id = ss.session_exercise_id "
        "   WHERE se.session_id = s.id) AS volume_kg "
        "FROM workout_sessions s WHERE s.user_id = ? AND s.finished_at IS NOT NULL"
    )
    params = [user_id]
    if start_utc:
        sql += " AND s.started_at >= ?"
        params.append(start_utc)
    if end_utc:
        sql += " AND s.started_at < ?"
        params.append(end_utc)
    sql += " ORDER BY s.started_at DESC, s.id DESC"
    return query_all(sql, tuple(params))


def body_weights(user_id, day_from=None, day_to=None):
    sql = "SELECT id, entry_date, weight_kg FROM body_weights WHERE user_id = ?"
    params = [user_id]
    if day_from:
        sql += " AND entry_date >= ?"
        params.append(day_from)
    if day_to:
        sql += " AND entry_date <= ?"
        params.append(day_to)
    sql += " ORDER BY entry_date DESC"
    return query_all(sql, tuple(params))


# ------------------------------------------------------------------ history

@bp.route("/history")
@login_required
def index():
    raw_from, raw_to = request.args.get("from", ""), request.args.get("to", "")
    day_from = parse_date(raw_from) if raw_from else None
    day_to = parse_date(raw_to) if raw_to else None
    errors = {}
    if raw_from and day_from is None:
        errors["from"] = "Enter a valid start date."
    if raw_to and day_to is None:
        errors["to"] = "Enter a valid end date."
    if day_from and day_to and day_from > day_to:
        errors["to"] = "The end date must be on or after the start date."
    if errors:
        day_from = day_to = None
    unit = weight_unit(g.user["id"])
    sessions = finished_sessions(g.user["id"], *local_day_bounds_utc(day_from, day_to))
    for s in sessions:
        s["volume"] = fmt_weight(s["volume_kg"], unit)
    weights = body_weights(g.user["id"], day_from, day_to)
    for w in weights:
        w["weight"] = fmt_weight(w["weight_kg"], unit)
    return render_template(
        "history/index.html", sessions=sessions, weights=weights, unit=unit,
        raw_from=raw_from, raw_to=raw_to, errors=errors,
        filtered=bool(day_from or day_to), status=400 if errors else 200,
    ), 400 if errors else 200


# ------------------------------------------------------------------ body weight

def _get_entry(entry_id):
    row = query_one("SELECT * FROM body_weights WHERE id = ? AND user_id = ?",
                    (entry_id, g.user["id"]))
    if row is None:
        abort(404)
    return row


def _parse_entry(form, unit):
    errors = {}
    day = parse_date(form.get("entry_date"))
    if day is None:
        errors["entry_date"] = "Enter a valid date."
    elif day > local_today():
        errors["entry_date"] = "The date can't be in the future."
    low, high = BODY_WEIGHT_RANGE[unit]
    weight = parse_float(form.get("weight"), low, high)
    if weight is None:
        errors["weight"] = f"Enter a weight between {low} and {high} {unit}."
    if errors:
        return None, errors
    return (day, round(to_kg(weight, unit), 2)), {}


def _render_body(unit, errors=None, form=None, edit_id=None, status=200):
    entries = body_weights(g.user["id"])
    for e in entries:
        e["weight"] = fmt_weight(e["weight_kg"], unit)
    form = form or {"entry_date": local_today().isoformat(), "weight": ""}
    return render_template("history/body_weight.html", entries=entries, unit=unit,
                           errors=errors or {}, form=form, edit_id=edit_id,
                           today=local_today().isoformat()), status


@bp.route("/body-weight", methods=("GET", "POST"))
@login_required
def body_weight():
    unit = weight_unit(g.user["id"])
    if request.method == "GET":
        return _render_body(unit, edit_id=request.args.get("edit", type=int))
    values, errors = _parse_entry(request.form, unit)
    if not errors:
        day, kg = values
        if query_one("SELECT id FROM body_weights WHERE user_id = ? AND entry_date = ?",
                     (g.user["id"], day)):
            errors["entry_date"] = "You already logged a weight for this date. Edit that entry instead."
        else:
            try:
                execute("INSERT INTO body_weights (user_id, entry_date, weight_kg) VALUES (?, ?, ?)",
                        (g.user["id"], day, kg))
            except integrity_errors():
                errors["entry_date"] = "You already logged a weight for this date."
            else:
                flash("Body weight logged.", "success")
                return redirect(url_for("history.body_weight"))
    return _render_body(unit, errors, dict(request.form), status=400)


@bp.route("/body-weight/<int:entry_id>", methods=("POST",))
@login_required
def update_body_weight(entry_id):
    entry = _get_entry(entry_id)
    unit = weight_unit(g.user["id"])
    values, errors = _parse_entry(request.form, unit)
    if not errors:
        day, kg = values
        clash = query_one("SELECT id FROM body_weights WHERE user_id = ? AND entry_date = ? "
                          "AND id <> ?", (g.user["id"], day, entry["id"]))
        if clash:
            errors["entry_date"] = "Another entry already uses this date."
        else:
            execute("UPDATE body_weights SET entry_date = ?, weight_kg = ? WHERE id = ?",
                    (day, kg, entry["id"]))
            flash("Entry updated.", "success")
            return redirect(url_for("history.body_weight"))
    for message in errors.values():
        flash(message, "error")
    return redirect(url_for("history.body_weight", edit=entry_id))


@bp.route("/body-weight/<int:entry_id>/delete", methods=("GET", "POST"))
@login_required
def delete_body_weight(entry_id):
    entry = _get_entry(entry_id)
    if request.method == "POST":
        execute("DELETE FROM body_weights WHERE id = ?", (entry["id"],))
        flash("Entry deleted.", "success")
        return redirect(url_for("history.body_weight"))
    unit = weight_unit(g.user["id"])
    return render_template(
        "confirm.html", title="Delete entry",
        message=f"Delete the {fmt_weight(entry['weight_kg'], unit)} {unit} entry for "
                f"{entry['entry_date']:%b} {entry['entry_date'].day}, {entry['entry_date'].year}?",
        action=url_for("history.delete_body_weight", entry_id=entry_id),
        button="Delete entry", cancel=url_for("history.body_weight"))
