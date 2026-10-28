import hashlib
import os
import re
import secrets
import sqlite3
import time
from functools import wraps

from flask import jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(BASE_DIR)
DEFAULT_DATABASE_PATH = os.path.join(BACKEND_DIR, "instance", "auth.sqlite3")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESSION_COOKIE_NAME = "agri_session"
SESSION_DURATION_SECONDS = 7 * 24 * 60 * 60


class AuthService:
    def __init__(self, database_path=None):
        if database_path is not None:
            self.database_path = os.fspath(database_path)
        elif "DATABASE_PATH" in os.environ:
            self.database_path = os.environ["DATABASE_PATH"]
        elif "AGRI_AUTH_DB" in os.environ:
            self.database_path = os.environ["AGRI_AUTH_DB"]
        else:
            self.database_path = DEFAULT_DATABASE_PATH

        if not self.database_path:
            raise ValueError("The authentication database path cannot be empty.")
        if os.path.isdir(self.database_path):
            raise ValueError(
                f"The authentication database path '{self.database_path}' is a directory; "
                "set DATABASE_PATH to a SQLite file path, for example /var/data/auth.sqlite3."
            )

        database_directory = os.path.dirname(os.path.abspath(self.database_path))
        try:
            os.makedirs(database_directory, exist_ok=True)
        except OSError as error:
            raise RuntimeError(
                f"Cannot create authentication database directory "
                f"'{database_directory}' for DATABASE_PATH='{self.database_path}': {error}"
            ) from error
        self.initialize_database()

    def connect(self):
        connection = None
        try:
            connection = sqlite3.connect(self.database_path, timeout=10)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            return connection
        except sqlite3.Error as error:
            if connection is not None:
                connection.close()
            raise RuntimeError(
                f"Cannot open authentication database at "
                f"'{self.database_path}'; check DATABASE_PATH and filesystem "
                f"permissions: {error}"
            ) from error

    def initialize_database(self):
        try:
            with self.connect() as connection:
                connection.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                        password_hash TEXT NOT NULL,
                        created_at INTEGER NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS auth_sessions (
                        token_hash TEXT PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        expires_at INTEGER NOT NULL
                    );

                    CREATE INDEX IF NOT EXISTS auth_sessions_expiry_idx
                        ON auth_sessions(expires_at);
                    """
                )
        except sqlite3.Error as error:
            raise RuntimeError(
                f"Cannot initialize authentication database at "
                f"'{self.database_path}': {error}"
            ) from error

    @staticmethod
    def normalize_email(email):
        if not isinstance(email, str):
            return None
        normalized = email.strip().lower()
        if len(normalized) > 254 or not EMAIL_PATTERN.fullmatch(normalized):
            return None
        return normalized

    def register(self, email, password):
        normalized_email = self.normalize_email(email)
        if normalized_email is None:
            return None, "Enter a valid email address."
        if not isinstance(password, str) or not 8 <= len(password) <= 128:
            return None, "Password must be between 8 and 128 characters."

        password_hash = generate_password_hash(password)
        try:
            with self.connect() as connection:
                cursor = connection.execute(
                    "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
                    (normalized_email, password_hash, int(time.time())),
                )
                user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            return None, "An account with this email already exists."

        return {"id": user_id, "email": normalized_email}, None

    def authenticate(self, email, password):
        normalized_email = self.normalize_email(email)
        if normalized_email is None or not isinstance(password, str):
            return None

        with self.connect() as connection:
            user = connection.execute(
                "SELECT id, email, password_hash FROM users WHERE email = ?",
                (normalized_email,),
            ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            return None
        return {"id": user["id"], "email": user["email"]}

    def create_session(self, user_id):
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        expires_at = int(time.time()) + SESSION_DURATION_SECONDS

        with self.connect() as connection:
            connection.execute(
                "DELETE FROM auth_sessions WHERE expires_at <= ?", (int(time.time()),)
            )
            connection.execute(
                "INSERT INTO auth_sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                (token_hash, user_id, expires_at),
            )
        return token

    def get_user_for_token(self, token):
        if not isinstance(token, str) or not token:
            return None

        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        now = int(time.time())
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT users.id, users.email, auth_sessions.expires_at
                FROM auth_sessions
                JOIN users ON users.id = auth_sessions.user_id
                WHERE auth_sessions.token_hash = ?
                """,
                (token_hash,),
            ).fetchone()
            if row is not None and row["expires_at"] <= now:
                connection.execute(
                    "DELETE FROM auth_sessions WHERE token_hash = ?", (token_hash,)
                )
                return None

        if row is None:
            return None
        return {"id": row["id"], "email": row["email"]}

    def delete_session(self, token):
        if not isinstance(token, str) or not token:
            return
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM auth_sessions WHERE token_hash = ?", (token_hash,)
            )


auth_service = AuthService()


def require_auth(handler):
    @wraps(handler)
    def wrapped(*args, **kwargs):
        user = auth_service.get_user_for_token(
            request.cookies.get(SESSION_COOKIE_NAME)
        )
        if user is None:
            return jsonify({"error": "Please log in to continue."}), 401
        request.auth_user = user
        return handler(*args, **kwargs)

    return wrapped
