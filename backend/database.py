import os
import sqlite3
import time

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()
BASE_DIR = os.path.dirname(__file__)
SQLITE_DB_PATH = os.path.join(BASE_DIR, "cloudproof.db")
SQLITE_INITIALIZED = False


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT,
    role_arn TEXT,
    credential_type TEXT CHECK(credential_type IN ('access_key', 'role_arn') OR credential_type IS NULL),
    aws_access_key_encrypted TEXT,
    aws_secret_key_encrypted TEXT,
    cloudtrail_bucket TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Migrations: add new columns if they don't exist (for existing DBs)

CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    service TEXT NOT NULL,
    action TEXT NOT NULL,
    score INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS daily_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    total_score INTEGER NOT NULL,
    UNIQUE(user_id, date),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS processing_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    last_processed_timestamp TIMESTAMP NOT NULL,
    UNIQUE(user_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_activity_logs_user_date
    ON activity_logs(user_id, date);

CREATE INDEX IF NOT EXISTS idx_daily_scores_user_date
    ON daily_scores(user_id, date);

CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


def get_db_connection(retries=3):
    """
    Return a database connection.

    By default, local development uses SQLite backed by cloudproof.db
    in the backend folder. PostgreSQL remains available and can be
    selected by setting DB_ENGINE=postgres.
    """
    engine = DB_ENGINE
    if engine == "sqlite":
        return _get_sqlite_connection()
    else:
        return _get_postgres_connection(retries=retries)


def _get_postgres_connection(retries=3):
    for attempt in range(retries):
        try:
            return psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                database=os.getenv("DB_NAME", "cloudproof"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", "postgres"),
                connect_timeout=10,
            )
        except psycopg2.OperationalError as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            raise Exception(
                f"Database connection failed after {retries} attempts: {str(e)}"
            )


def _get_sqlite_connection():
    """Return a SQLite connection and ensure schema exists."""
    global SQLITE_INITIALIZED

    conn = sqlite3.connect(
        SQLITE_DB_PATH,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
    )
    conn.row_factory = sqlite3.Row

    # Enforce foreign key constraints in SQLite
    conn.execute("PRAGMA foreign_keys = ON;")

    if not SQLITE_INITIALIZED:
        _init_sqlite_schema(conn)
        SQLITE_INITIALIZED = True

    return conn


def _init_sqlite_schema(conn: sqlite3.Connection):
    """Create all required tables if they do not already exist. Run migrations for existing DBs."""
    conn.executescript(SQLITE_SCHEMA)
    # Migrations: add new auth/credentials columns to existing users table
    _run_sqlite_migrations(conn)
    conn.commit()


def _run_sqlite_migrations(conn: sqlite3.Connection):
    """Add new columns to users table if they don't exist (for existing installations)."""
    migrations = [
        ("password_hash", "ALTER TABLE users ADD COLUMN password_hash TEXT"),
        ("credential_type", "ALTER TABLE users ADD COLUMN credential_type TEXT"),
        ("aws_access_key_encrypted", "ALTER TABLE users ADD COLUMN aws_access_key_encrypted TEXT"),
        ("aws_secret_key_encrypted", "ALTER TABLE users ADD COLUMN aws_secret_key_encrypted TEXT"),
        ("cloudtrail_bucket", "ALTER TABLE users ADD COLUMN cloudtrail_bucket TEXT"),
    ]
    cursor = conn.cursor()
    for col_name, stmt in migrations:
        try:
            cursor.execute("SELECT 1 FROM pragma_table_info('users') WHERE name=?", (col_name,))
            if cursor.fetchone():
                continue
            cursor.execute(stmt)
        except sqlite3.OperationalError:
            pass  # Column may already exist
    cursor.close()


def _convert_sqlite_placeholders(query, params):
    """
    Convert psycopg2-style %s placeholders to SQLite ? placeholders.
    """
    if params is None:
        return query, None

    if "%s" in query:
        query = query.replace("%s", "?")

    # Ensure params is a sequence type that SQLite understands
    if not isinstance(params, (list, tuple)):
        params = [params]

    return query, params


def execute_query(query, params=None, fetch=False):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()

        if DB_ENGINE == "sqlite":
            query, params = _convert_sqlite_placeholders(query, params)
            cursor = conn.cursor()
            cursor.execute(query, params or [])
            if fetch:
                rows = cursor.fetchall()
                result = [dict(row) for row in rows]
            else:
                result = None
        else:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params)
            result = cursor.fetchall() if fetch else None

        conn.commit()
        return result
    except Exception as e:
        if conn:
            conn.rollback()
        raise Exception(f"Query execution failed: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
