-- SQL Script for Fitness Tracker Database Setup
-- Database System: PostgreSQL

-- =================================================================
-- I. DATA DEFINITION LANGUAGE (DDL) - CREATING TABLES
-- =================================================================

-- Drop tables in reverse order of dependency to ensure clean setup if they already exist.
-- Useful for resetting the database during development.
-- DROP TABLE IF EXISTS goals;
-- DROP TABLE IF EXISTS exercises;
-- DROP TABLE IF EXISTS workouts;
-- DROP TABLE IF EXISTS friends;
-- DROP TABLE IF EXISTS users;

-- Table to store user profile information
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    weight_kg NUMERIC(5, 2)
);

-- Table to manage friendships (many-to-many relationship between users)
CREATE TABLE IF NOT EXISTS friends (
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    friend_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, friend_id)
);

-- Table to store workout session logs
CREATE TABLE IF NOT EXISTS workouts (
    workout_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    workout_date DATE NOT NULL,
    duration_minutes INTEGER
);

-- Table to store details of exercises performed in a workout
CREATE TABLE IF NOT EXISTS exercises (
    exercise_id SERIAL PRIMARY KEY,
    workout_id INTEGER NOT NULL REFERENCES workouts(workout_id) ON DELETE CASCADE,
    exercise_name VARCHAR(255) NOT NULL,
    sets INTEGER,
    reps INTEGER,
    weight_kg NUMERIC(6, 2)
);

-- Table to store personal fitness goals
CREATE TABLE IF NOT EXISTS goals (
    goal_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    goal_description TEXT,
    target_value INTEGER,
    start_date DATE DEFAULT CURRENT_DATE,
    end_date DATE,
    is_active BOOLEAN DEFAULT TRUE
);


-- =================================================================
-- II. DATA MANIPULATION LANGUAGE (DML) - SEEDING DATA
-- =================================================================

-- Clear existing data to prevent duplicates on re-run
TRUNCATE TABLE users, friends, workouts, exercises, goals RESTART IDENTITY CASCADE;

-- Insert sample users
-- The main user for the application will be Alice (user_id=1)
INSERT INTO users (name, email, weight_kg) VALUES
('Alice', 'alice@email.com', 60.50),
('Bob', 'bob@email.com', 85.00),
('Charlie', 'charlie@email.com', 72.30),
('Diana', 'diana@email.com', 55.00);

-- Insert sample friendships for the main user (Alice)
-- Alice is friends with Bob and Diana
INSERT INTO friends (user_id, friend_id) VALUES
(1, 2),  -- Alice -> Bob
(1, 4);  -- Alice -> Diana

-- Insert sample workouts
-- Note: CURRENT_DATE is assumed to be 2025-08-21 for this example.
-- These dates ensure the leaderboard shows activity for the "current week".
INSERT INTO workouts (user_id, workout_date, duration_minutes) VALUES
(1, '2025-08-19', 60),  -- Alice's workout (workout_id=1)
(2, '2025-08-18', 75),  -- Bob's workout (workout_id=2)
(4, '2025-08-20', 45),  -- Diana's workout (workout_id=3)
(1, '2025-08-21', 55),  -- Alice's second workout (workout_id=4)
(3, '2025-08-15', 90);  -- Charlie's workout (last week, won't appear on leaderboard)

-- Insert sample exercises linked to the workouts above
INSERT INTO exercises (workout_id, exercise_name, sets, reps, weight_kg) VALUES
-- Exercises for Alice's first workout (ID 1)
(1, 'Bench Press', 3, 10, 50.0),
(1, 'Squat', 4, 8, 80.0),

-- Exercises for Bob's workout (ID 2)
(2, 'Running', 1, 1, 0), -- Using 0 weight for cardio
(2, 'Pull-ups', 5, 5, 0), -- Bodyweight exercise

-- Exercises for Diana's workout (ID 3)
(3, 'Yoga Flow', 1, 1, 0),

-- Exercises for Alice's second workout (ID 4)
(4, 'Bench Press', 3, 12, 52.5),
(4, 'Deadlift', 3, 6, 100.0),

-- Exercises for Charlie's workout (ID 5)
(5, 'Leg Press', 4, 12, 150.0),
(5, 'Bicep Curls', 3, 15, 15.0);

-- Insert a sample goal for the main user (Alice)
INSERT INTO goals (user_id, goal_description, target_value) VALUES
(1, 'Workout 3 times a week', 3);

-- =================================================================
-- SCRIPT COMPLETE
-- =================================================================