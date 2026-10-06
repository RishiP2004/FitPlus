"""Fitness & Workout Tracker — Flask application factory."""
import os
from datetime import timedelta
from pathlib import Path

from flask import Flask, g, render_template, session

from . import db
from .security import csrf_protect, csrf_token


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    database_url = os.environ.get("DATABASE_URL", "")
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-only-change-me"),
        DATABASE_URL=database_url,
        DATABASE_PATH=os.environ.get(
            "DATABASE_PATH", str(Path(app.instance_path) / "fitness.sqlite3")
        ),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
        AUTO_INIT_DB=os.environ.get("AUTO_INIT_DB", "1") == "1",
    )
    if test_config:
        app.config.update(test_config)

    if app.config["SECRET_KEY"] == "dev-only-change-me" and not app.debug and not app.testing:
        app.logger.warning("SECRET_KEY is not set. Set it in the environment before deploying.")

    db.init_app(app)

    from . import auth, exercises, main, profile

    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(profile.bp)
    app.register_blueprint(exercises.bp)

    app.before_request(csrf_protect)
    app.before_request(auth.load_logged_in_user)
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "same-origin")
        return resp

    @app.errorhandler(400)
    @app.errorhandler(404)
    def error_page(err):
        return render_template("error.html", error=err), err.code

    if app.config["AUTO_INIT_DB"]:
        with app.app_context():
            db.init_db()

    return app
