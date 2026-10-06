-- Sprint 1: users, profiles, exercise library (SQLite)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash VARCHAR(100) NOT NULL,
    is_admin BOOLEAN NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    age INTEGER,
    height_cm REAL,
    weight_kg REAL,
    fitness_level VARCHAR(20),
    goal VARCHAR(40),
    unit_system VARCHAR(10) NOT NULL DEFAULT 'metric',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    muscle_group VARCHAR(40) NOT NULL,
    equipment VARCHAR(40) NOT NULL,
    instructions TEXT NOT NULL,
    is_preset BOOLEAN NOT NULL DEFAULT 1,
    created_by INTEGER REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_exercises_muscle ON exercises (muscle_group);
CREATE INDEX idx_exercises_equipment ON exercises (equipment);
CREATE UNIQUE INDEX idx_exercises_preset_name ON exercises (name) WHERE created_by IS NULL;
