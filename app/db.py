"""Database access for SQLite (local dev/tests) and PostgreSQL (hosted).

Set DATABASE_URL to a postgres:// or postgresql:// URL to use PostgreSQL.
Otherwise the app uses a SQLite file (DATABASE_PATH, default instance/fitness.sqlite3).

All SQL in the app uses "?" placeholders; they are converted to "%s" for PostgreSQL.
"""
import os
import sqlite3
from pathlib import Path

import click
from flask import current_app, g

SCHEMA_DIR = Path(__file__).parent / "schema"


def _is_postgres(url):
    return bool(url) and url.startswith(("postgres://", "postgresql://"))


def is_postgres():
    return _is_postgres(current_app.config.get("DATABASE_URL"))


def integrity_errors():
    """Exception classes raised on UNIQUE / FK violations for the active driver."""
    errors = [sqlite3.IntegrityError]
    try:
        import psycopg

        errors.append(psycopg.errors.IntegrityError)
    except ImportError:
        pass
    return tuple(errors)


def _connect():
    url = current_app.config.get("DATABASE_URL")
    if _is_postgres(url):
        import psycopg
        from psycopg.rows import dict_row

        # Some hosts hand out postgres://; psycopg accepts both.
        return psycopg.connect(url, row_factory=dict_row)
    path = current_app.config["DATABASE_PATH"]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def get_db():
    if "db" not in g:
        g.db = _connect()
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def _sql(sql):
    return sql.replace("?", "%s") if is_postgres() else sql


def _row(row):
    return dict(row) if row is not None else None


def query_all(sql, params=()):
    cur = get_db().execute(_sql(sql), params)
    return [_row(r) for r in cur.fetchall()]


def query_one(sql, params=()):
    cur = get_db().execute(_sql(sql), params)
    return _row(cur.fetchone())


def execute(sql, params=(), commit=True):
    """Run a write. Returns the first row if the statement has RETURNING."""
    conn = get_db()
    try:
        cur = conn.execute(_sql(sql), params)
        row = cur.fetchone() if cur.description else None
        if commit:
            conn.commit()
        return _row(row)
    except Exception:
        conn.rollback()
        raise


# ---------------------------------------------------------------- migrations

def _migration_files():
    suffix = "postgres" if is_postgres() else "sqlite"
    return sorted(SCHEMA_DIR.glob(f"*.{suffix}.sql"))


def migrate():
    """Apply any schema files not yet recorded in schema_migrations."""
    conn = get_db()
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (version VARCHAR(100) PRIMARY KEY)"
    )
    conn.commit()
    applied = {r["version"] for r in query_all("SELECT version FROM schema_migrations")}
    ran = []
    for path in _migration_files():
        version = path.name.split(".")[0]
        if version in applied:
            continue
        script = path.read_text()
        if is_postgres():
            conn.execute(script)
        else:
            conn.executescript(script)
        conn.execute(_sql("INSERT INTO schema_migrations (version) VALUES (?)"), (version,))
        conn.commit()
        ran.append(version)
    return ran


def init_db():
    from .seed import seed_exercises

    ran = migrate()
    added = seed_exercises()
    return ran, added


@click.command("init-db")
def init_db_command():
    """Create/upgrade tables and seed the preset exercise library."""
    ran, added = init_db()
    click.echo(f"Migrations applied: {', '.join(ran) or 'none'}")
    click.echo(f"Preset exercises added: {added}")


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
