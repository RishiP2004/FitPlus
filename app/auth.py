"""Registration, login and logout (PB-04 to PB-07)."""
import re
from urllib.parse import urlparse

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for

from .db import execute, integrity_errors, query_one
from .security import dummy_verify, hash_password, verify_password

bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
MIN_PASSWORD = 8
MAX_PASSWORD = 72  # bcrypt only uses the first 72 bytes


def load_logged_in_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id is not None:
        g.user = query_one("SELECT id, email, is_admin FROM users WHERE id = ?", (user_id,))
        if g.user is None:  # account no longer exists
            session.clear()


def validate_registration(email, password, confirm):
    errors = {}
    if not email:
        errors["email"] = "Email is required."
    elif len(email) > 254 or not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address, like name@example.com."
    if len(password) < MIN_PASSWORD:
        errors["password"] = f"Password must be at least {MIN_PASSWORD} characters."
    elif len(password.encode("utf-8")) > MAX_PASSWORD:
        errors["password"] = f"Password must be at most {MAX_PASSWORD} characters."
    if not errors.get("password") and password != confirm:
        errors["confirm"] = "Passwords do not match."
    return errors


def _start_session(user_id):
    session.clear()  # new session id on login: prevents session fixation
    session["user_id"] = user_id
    session.permanent = True


def _safe_next(target):
    if not target:
        return None
    parts = urlparse(target)
    if parts.scheme or parts.netloc or not target.startswith("/") or target.startswith("//"):
        return None
    return target


@bp.route("/register", methods=("GET", "POST"))
def register():
    if g.user:
        return redirect(url_for("main.dashboard"))
    form = {"email": ""}
    errors = {}
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        form["email"] = email
        errors = validate_registration(email, password, confirm)
        if not errors and query_one("SELECT id FROM users WHERE email = ?", (email,)):
            errors["email"] = "An account with this email already exists. Try logging in."
        if not errors:
            try:
                row = execute(
                    "INSERT INTO users (email, password_hash) VALUES (?, ?) RETURNING id",
                    (email, hash_password(password)),
                )
            except integrity_errors():  # two sign-ups at the same moment
                errors["email"] = "An account with this email already exists. Try logging in."
            else:
                _start_session(row["id"])
                flash("Account created. Set up your profile to get started.", "success")
                return redirect(url_for("profile.edit", welcome=1))
        status = 400
        return render_template("auth/register.html", form=form, errors=errors), status
    return render_template("auth/register.html", form=form, errors=errors)


@bp.route("/login", methods=("GET", "POST"))
def login():
    if g.user:
        return redirect(url_for("main.dashboard"))
    next_url = _safe_next(request.values.get("next"))
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = query_one("SELECT id, password_hash FROM users WHERE email = ?", (email,))
        if user is None:
            dummy_verify(password)
        elif verify_password(password, user["password_hash"]):
            _start_session(user["id"])
            return redirect(next_url or url_for("main.dashboard"))
        flash("Incorrect email or password.", "error")
        return render_template("auth/login.html", email=email, next_url=next_url), 401
    return render_template("auth/login.html", email=email, next_url=next_url)


@bp.route("/logout", methods=("POST",))
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
