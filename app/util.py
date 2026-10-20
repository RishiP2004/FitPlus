"""Small helpers shared by the Sprint 2 features: units, times and form parsing."""
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from flask import current_app

from .db import query_one

KG_PER_LB = 0.45359237


# ----------------------------------------------------------------- units

def weight_unit(user_id):
    """'kg' or 'lb', from the user's profile (metric if no profile yet)."""
    row = query_one("SELECT unit_system FROM profiles WHERE user_id = ?", (user_id,))
    return "lb" if row and row["unit_system"] == "imperial" else "kg"


def to_kg(value, unit):
    return value * KG_PER_LB if unit == "lb" else value


def from_kg(value_kg, unit):
    if value_kg is None:
        return None
    return value_kg / KG_PER_LB if unit == "lb" else value_kg


def fmt_weight(value_kg, unit):
    """Display weight rounded to 0.1 and without a trailing .0 (e.g. 60, 62.5)."""
    v = round(from_kg(value_kg, unit), 1)
    return f"{v:g}"


# ----------------------------------------------------------------- times
# Times are stored in UTC without a timezone; they are shown in DISPLAY_TZ.

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _tz():
    return ZoneInfo(current_app.config.get("DISPLAY_TZ", "America/Toronto"))


def to_local(dt_utc):
    if dt_utc is None:
        return None
    return dt_utc.replace(tzinfo=timezone.utc).astimezone(_tz())


def local_today():
    return datetime.now(_tz()).date()


def local_day_bounds_utc(day_from=None, day_to=None):
    """UTC [start, end) bounds for local calendar days day_from..day_to (inclusive)."""
    tz = _tz()

    def utc(d):
        return datetime(d.year, d.month, d.day, tzinfo=tz).astimezone(timezone.utc).replace(tzinfo=None)

    start = utc(day_from) if day_from else None
    end = utc(day_to + timedelta(days=1)) if day_to else None
    return start, end


def fmt_local(dt_utc, with_time=True):
    """'Oct 20, 2026 6:05 PM' in the display timezone (portable, no %-d)."""
    if dt_utc is None:
        return ""
    d = to_local(dt_utc)
    text = f"{d:%b} {d.day}, {d.year}"
    if with_time:
        hour = d.hour % 12 or 12
        text += f" {hour}:{d:%M} {'AM' if d.hour < 12 else 'PM'}"
    return text


def fmt_duration(seconds):
    if seconds is None:
        return "–"
    seconds = int(seconds)
    if seconds < 60:
        return "<1 min"
    h, rem = divmod(seconds, 3600)
    m = rem // 60
    return f"{h} h {m} min" if h else f"{m} min"


# ----------------------------------------------------------------- parsing

def parse_int(raw, low, high):
    try:
        value = int(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return value if low <= value <= high else None


def parse_float(raw, low, high):
    try:
        value = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    return value if low <= value <= high else None


def parse_date(raw):
    try:
        return date.fromisoformat(str(raw).strip())
    except (TypeError, ValueError):
        return None


def init_app(app):
    app.config.setdefault("DISPLAY_TZ", "America/Toronto")
    app.jinja_env.filters["local"] = fmt_local
    app.jinja_env.filters["duration"] = fmt_duration
