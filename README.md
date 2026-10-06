# FitPlus — Fitness & Workout Tracker

CPS714 Group 11 project. A responsive web app to plan workouts, log sessions and track progress.

**Stack:** Python 3.10+ · Flask · SQLite (local) / PostgreSQL (hosted) · bcrypt · GitHub Actions · Render

## Sprint 1 (Sep 28 – Oct 9) — what's in this release

| ID | Story | Where |
|---|---|---|
| PB-01 | Git repo with branch protection on `main` | GitHub settings (see setup below) + PR template |
| PB-02 | CI pipeline: build + tests on every PR | `.github/workflows/ci.yml` (SQLite and PostgreSQL jobs) |
| PB-03 | Database, hosting, starter page | `app/db.py`, `app/schema/`, `render.yaml`, `/` and `/health` |
| PB-04 | Registration form with validation | `app/auth.py`, `templates/auth/register.html` |
| PB-05 | bcrypt password hashing, duplicate email check | `app/security.py`, `app/auth.py` |
| PB-06 | Login | `app/auth.py` |
| PB-07 | Logout, protected pages redirect to login | `app/auth.py`, `login_required` |
| PB-08 | Fitness profile with kg/lb units | `app/profile.py`, `templates/profile.html` |
| PB-09 | 58 preset exercises seeded | `app/seed.py` |
| PB-10 | Browse grouped by muscle group | `/exercises/` |
| PB-11 | Exercise detail with instructions | `/exercises/<id>` |
| PB-12 | Search by name (live, in-browser) | `static/exercises.js` |
| PB-13 | Filter by muscle group + equipment, combined with search | `/exercises/` |

Each story's acceptance criteria are tested in `tests/` (36 tests).

## Run it locally

```bash
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
flask --app wsgi run --debug         # http://127.0.0.1:5000
```

The SQLite database is created and seeded automatically in `instance/fitness.sqlite3`.
To reset it, delete that file. To migrate/seed by hand: `flask --app wsgi init-db`.

## Run the tests

```bash
pytest -q --cov=app
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | dev value | Signs session cookies. **Must** be set in production. |
| `DATABASE_URL` | empty (SQLite) | `postgresql://...` to use PostgreSQL |
| `DATABASE_PATH` | `instance/fitness.sqlite3` | SQLite file location |
| `SESSION_COOKIE_SECURE` | `0` | Set `1` behind HTTPS |
| `AUTO_INIT_DB` | `1` | Migrate + seed on startup |

## One-time setup (Sprint 1 tasks that need a person)

1. **Push the code**: `git push -u origin sprint-1`, then open a pull request into `main`.
2. **Branch protection (PB-01)**: GitHub repo → Settings → Branches → Add rule for `main`:
   tick *Require a pull request before merging* (1 approval) and *Require status checks to pass*,
   then pick **Tests (SQLite)** and **Tests (PostgreSQL)**. Add teammates under Settings → Collaborators.
3. **CI (PB-02)**: runs automatically once the workflow is on GitHub. Check the *Actions* tab.
4. **Hosting + database (PB-03)**: sign in to [render.com](https://render.com) with GitHub →
   New → Blueprint → pick this repo. Render creates the web service and PostgreSQL database from
   `render.yaml`. When it's live, open `https://<your-service>.onrender.com/health` — it should show
   `"database": "ok"`. Put that URL in the team docs as the test URL.

## Project layout

```
app/            Flask app (blueprints: main, auth, profile, exercises)
  schema/       SQL migrations (SQLite + PostgreSQL)
  templates/    Jinja pages
  static/       CSS + JS
tests/          unittest/pytest suite, one file per area
wsgi.py         Entry point
render.yaml     Hosting blueprint
```
