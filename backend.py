# backend.py

import psycopg2
from psycopg2 import sql
import datetime

# --- DATABASE CONNECTION ---
# IMPORTANT: Replace with your actual PostgreSQL credentials
DB_CONFIG = {
    "dbname": "fitnessdb",
    "user": "postgres",
    "password": "Admin@0416",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"Error connecting to the database: {e}")
        return None

# --- DATABASE INITIALIZATION ---
def initialize_database():
    """Creates all necessary tables if they don't exist."""
    conn = get_db_connection()
    if not conn:
        return
        
    commands = [
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            weight_kg NUMERIC(5, 2)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS friends (
            user_id INTEGER REFERENCES users(user_id),
            friend_id INTEGER REFERENCES users(user_id),
            PRIMARY KEY (user_id, friend_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS workouts (
            workout_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id),
            workout_date DATE NOT NULL,
            duration_minutes INTEGER
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS exercises (
            exercise_id SERIAL PRIMARY KEY,
            workout_id INTEGER NOT NULL REFERENCES workouts(workout_id) ON DELETE CASCADE,
            exercise_name VARCHAR(255) NOT NULL,
            sets INTEGER,
            reps INTEGER,
            weight_kg NUMERIC(6, 2)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS goals (
            goal_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id),
            goal_description TEXT,
            target_value INTEGER,
            start_date DATE DEFAULT CURRENT_DATE,
            end_date DATE,
            is_active BOOLEAN DEFAULT TRUE
        )
        """
    ]
    try:
        with conn.cursor() as cur:
            for command in commands:
                cur.execute(command)
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

# --- USER PROFILE (CRUD) ---
def get_user_profile(user_id):
    """READ: Fetches a user's profile."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT name, email, weight_kg FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()
    conn.close()
    return user

def update_user_profile(user_id, name, email, weight):
    """UPDATE: Updates a user's profile information."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET name = %s, email = %s, weight_kg = %s WHERE user_id = %s",
            (name, email, weight, user_id)
        )
        conn.commit()
    conn.close()

def get_all_users(exclude_user_id):
    """READ: Fetches all users, excluding the specified user."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT user_id, name FROM users WHERE user_id != %s", (exclude_user_id,))
        users = cur.fetchall()
    conn.close()
    return users

# --- WORKOUTS (CRUD) ---
def log_workout(user_id, date, duration, exercises):
    """CREATE: Logs a new workout and its associated exercises in a transaction."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Insert into workouts table
            cur.execute(
                "INSERT INTO workouts (user_id, workout_date, duration_minutes) VALUES (%s, %s, %s) RETURNING workout_id",
                (user_id, date, duration)
            )
            workout_id = cur.fetchone()[0]

            # Insert into exercises table
            for ex in exercises:
                cur.execute(
                    "INSERT INTO exercises (workout_id, exercise_name, sets, reps, weight_kg) VALUES (%s, %s, %s, %s, %s)",
                    (workout_id, ex['name'], ex['sets'], ex['reps'], ex['weight'])
                )
        conn.commit()
    except psycopg2.Error as e:
        print(f"Database error during workout log: {e}")
        conn.rollback()
    finally:
        conn.close()

def get_user_workouts(user_id):
    """READ: Fetches a history of workouts for a user."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT workout_id, workout_date, duration_minutes FROM workouts WHERE user_id = %s ORDER BY workout_date DESC",
            (user_id,)
        )
        workouts = cur.fetchall()
    conn.close()
    return workouts

def get_workout_details(workout_id):
    """READ: Fetches exercises for a specific workout."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT exercise_name, sets, reps, weight_kg FROM exercises WHERE workout_id = %s",
            (workout_id,)
        )
        details = cur.fetchall()
    conn.close()
    return details
    
# --- FRIENDS (CRUD) ---
def get_friends(user_id):
    """READ: Fetches a user's friends."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT u.user_id, u.name 
            FROM users u
            JOIN friends f ON u.user_id = f.friend_id
            WHERE f.user_id = %s
            """, (user_id,)
        )
        friends = cur.fetchall()
    conn.close()
    return friends

def add_friend(user_id, friend_id):
    """CREATE: Adds a friend connection."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("INSERT INTO friends (user_id, friend_id) VALUES (%s, %s)", (user_id, friend_id))
        conn.commit()
    conn.close()

def remove_friend(user_id, friend_id):
    """DELETE: Removes a friend connection."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM friends WHERE user_id = %s AND friend_id = %s", (user_id, friend_id))
        conn.commit()
    conn.close()
    
# --- GOALS (CRUD) ---
def set_goal(user_id, description, target_value):
    """CREATE: Sets a new fitness goal for the user."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        # Deactivate old goals of the same type if necessary
        cur.execute("UPDATE goals SET is_active = FALSE WHERE user_id = %s", (user_id,))
        cur.execute(
            "INSERT INTO goals (user_id, goal_description, target_value) VALUES (%s, %s, %s)",
            (user_id, description, target_value)
        )
        conn.commit()
    conn.close()
    
def get_active_goal(user_id):
    """READ: Fetches the current active goal for a user."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT goal_description, target_value FROM goals WHERE user_id = %s AND is_active = TRUE",
            (user_id,)
        )
        goal = cur.fetchone()
    conn.close()
    return goal
    
# --- BUSINESS INSIGHTS & LEADERBOARD ---
def get_leaderboard():
    """Calculates leaderboard data based on total workout minutes in the current week."""
    conn = get_db_connection()
    query = """
    SELECT
        u.name,
        COALESCE(SUM(w.duration_minutes), 0) AS total_minutes
    FROM
        users u
    LEFT JOIN
        workouts w ON u.user_id = w.user_id
    WHERE
        w.workout_date >= date_trunc('week', CURRENT_DATE)
    GROUP BY
        u.name
    ORDER BY
        total_minutes DESC;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        leaderboard = cur.fetchall()
    conn.close()
    return leaderboard

def get_workout_statistics(user_id):
    """Calculates aggregate statistics for a user's workouts."""
    conn = get_db_connection()
    stats = {}
    with conn.cursor() as cur:
        # COUNT: Total workouts
        cur.execute("SELECT COUNT(*) FROM workouts WHERE user_id = %s", (user_id,))
        stats['total_workouts'] = cur.fetchone()[0]

        # SUM: Total duration
        cur.execute("SELECT SUM(duration_minutes) FROM workouts WHERE user_id = %s", (user_id,))
        total_duration = cur.fetchone()[0]
        stats['total_duration'] = total_duration if total_duration else 0

        # AVG: Average duration
        cur.execute("SELECT AVG(duration_minutes) FROM workouts WHERE user_id = %s", (user_id,))
        avg_duration = cur.fetchone()[0]
        stats['avg_duration'] = round(avg_duration, 2) if avg_duration else 0
        
        # MIN/MAX weight for a specific exercise (e.g., 'Bench Press')
        cur.execute("""
            SELECT MIN(weight_kg), MAX(weight_kg) 
            FROM exercises 
            WHERE workout_id IN (SELECT workout_id FROM workouts WHERE user_id = %s)
            AND exercise_name = 'Bench Press'
            """, (user_id,))
        min_max_weight = cur.fetchone()
        stats['min_bench_press'] = min_max_weight[0] if min_max_weight else 0
        stats['max_bench_press'] = min_max_weight[1] if min_max_weight else 0

    conn.close()
    return stats

# --- SEEDING (for demonstration purposes) ---
def seed_data():
    """Adds some sample data to the database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Check if data exists
            cur.execute("SELECT COUNT(*) FROM users")
            if cur.fetchone()[0] > 0:
                return # Data already exists
            
            # Seed users
            users_to_add = [
                ('Alice', 'alice@email.com', 60.5),
                ('Bob', 'bob@email.com', 85.0),
                ('Charlie', 'charlie@email.com', 72.3),
                ('Diana', 'diana@email.com', 55.0)
            ]
            cur.executemany("INSERT INTO users (name, email, weight_kg) VALUES (%s, %s, %s)", users_to_add)

            # Seed friendships (Alice is friends with Bob and Diana)
            cur.execute("INSERT INTO friends (user_id, friend_id) VALUES (1, 2), (1, 4)")

            # Seed workouts for this week
            today = datetime.date.today()
            start_of_week = today - datetime.timedelta(days=today.weekday())
            
            workouts_to_add = [
                (1, start_of_week + datetime.timedelta(days=1), 60), # Alice
                (2, start_of_week + datetime.timedelta(days=0), 75), # Bob
                (4, start_of_week + datetime.timedelta(days=2), 45), # Diana
                (1, start_of_week + datetime.timedelta(days=3), 55)  # Alice
            ]
            cur.executemany("INSERT INTO workouts (user_id, workout_date, duration_minutes) VALUES (%s, %s, %s)", workouts_to_add)
            
            # Seed exercises
            exercises_to_add = [
                (1, 'Bench Press', 3, 10, 50.0), (1, 'Squat', 4, 8, 80.0), # Workout 1
                (2, 'Running', 1, 1, 0), (2, 'Pull-ups', 5, 5, 0), # Workout 2
                (3, 'Yoga', 1, 1, 0), # Workout 3
                (4, 'Bench Press', 3, 12, 52.5), (4, 'Deadlift', 3, 6, 100.0) # Workout 4
            ]
            cur.executemany("INSERT INTO exercises (workout_id, exercise_name, sets, reps, weight_kg) VALUES (%s, %s, %s, %s, %s)", exercises_to_add)

        conn.commit()
    except psycopg2.Error as e:
        print(f"Error seeding data: {e}")
        conn.rollback()
    finally:
        conn.close()