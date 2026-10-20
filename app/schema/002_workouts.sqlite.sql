-- Sprint 2: workout templates, workout sessions and sets, body weight (SQLite)
CREATE TABLE workout_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(60) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_templates_user ON workout_templates (user_id);

CREATE TABLE template_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL REFERENCES workout_templates(id) ON DELETE CASCADE,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    target_sets INTEGER NOT NULL,
    target_reps INTEGER NOT NULL
);
CREATE INDEX idx_template_exercises_template ON template_exercises (template_id, position);

CREATE TABLE workout_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    template_id INTEGER REFERENCES workout_templates(id) ON DELETE SET NULL,
    name VARCHAR(60) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    duration_seconds INTEGER,
    notes VARCHAR(500)
);
CREATE INDEX idx_sessions_user_started ON workout_sessions (user_id, started_at);

CREATE TABLE session_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    target_sets INTEGER,
    target_reps INTEGER
);
CREATE INDEX idx_session_exercises_session ON session_exercises (session_id, position);

CREATE TABLE session_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_exercise_id INTEGER NOT NULL REFERENCES session_exercises(id) ON DELETE CASCADE,
    set_number INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight_kg REAL NOT NULL
);
CREATE INDEX idx_session_sets_exercise ON session_sets (session_exercise_id, set_number);

CREATE TABLE body_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    entry_date DATE NOT NULL,
    weight_kg REAL NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, entry_date)
);
