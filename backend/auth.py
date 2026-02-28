"""
Authentication: password hashing and session helpers.
"""
import os
import functools
from flask import session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()


def hash_password(password: str) -> str:
    return generate_password_hash(password, method="scrypt")


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


def require_login(f):
    """Decorator: require user to be logged in. Injects user_id from session."""
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "Not authenticated. Please log in."}), 401
        return f(*args, user_id=user_id, **kwargs)
    return wrapped


def get_session_secret():
    return os.getenv("SECRET_KEY", "cloudproof-dev-secret-change-me")
