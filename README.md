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

## Sprint 2 (Oct 12 – Oct 23) — what's in this release (R1 – MVP)

| ID | Story | Where |
|---|---|---|
| PB-14 | Create and name a workout template | `/templates/`, `app/routines.py` |
| PB-15 | Add, reorder, remove exercises; target sets/reps | `/templates/<id>` |
| PB-16 | Edit (rename, change targets) and delete templates | `/templates/<id>`, confirm page |
| PB-17 | Start a workout from a template or blank | `/workouts/start`, `app/workouts.py` |
| PB-18 | Log sets, reps and weight under each exercise | `/workouts/<id>` |
| PB-19 | Finish and save a session with date and duration | Finish workout button |
| PB-20 | In-progress workout survives refresh; app returns to it | sets saved on add; `/`, login and banner resume it |
| PB-21 | Workout history, newest first; open a session for all sets | `/history`, `app/history.py` |
| PB-22 | Filter history by date range | `/history?from=…&to=…` |
| PB-23 | Edit logged sets in past sessions | Edit link on each set |
| PB-24 | Delete past sessions (with confirmation) | Delete this workout |
| PB-25 | Notes on sessions (up to 500 characters) | Notes box on the session page |
| PB-26 | Body weight: one entry per date, edit/delete, listed in history | `/body-weight` |

Weights are stored in kg and shown in the user's profile unit (kg or lb). Times are stored in UTC
and shown in `DISPLAY_TZ` (default America/Toronto). Sprint 2 tables are in `app/schema/002_*.sql`
and are applied automatically on start-up.

Each story's acceptance criteria are tested in `tests/` (89 tests: 36 from Sprint 1, 53 for Sprint 2).

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
| `DISPLAY_TZ` | `America/Toronto` | Timezone used to show times and filter history by date |

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
app/            Flask app (blueprints: main, auth, profile, exercises, routines, workouts, history)
  schema/       SQL migrations (SQLite + PostgreSQL)
  templates/    Jinja pages
  static/       CSS + JS
tests/          unittest/pytest suite, one file per area
wsgi.py         Entry point
render.yaml     Hosting blueprint
```
