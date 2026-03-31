"""
JWT-based authentication module.
Session-free — clients carry a signed token.
"""
import os
import functools
import logging
from datetime import datetime, timedelta, timezone

import jwt
from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return generate_password_hash(password, method="scrypt")


def verify_password(password_hash: str, password: str) -> bool:
    return check_password_hash(password_hash, password)


# ── Token helpers ─────────────────────────────────────────────────────────────

def _secret() -> str:
    key = os.getenv("SECRET_KEY", "cloudproof-dev-secret-change-in-production")
    if key == "cloudproof-dev-secret-change-in-production":
        logger.warning("SECRET_KEY not set — using insecure default. Set it in .env before production.")
    return key


def generate_token(user_id: int, expires_hours: int = 24) -> str:
    """Return a signed JWT that expires in `expires_hours` hours."""
    payload = {
        "user_id": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours),
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def decode_token(token: str) -> dict | None:
    """Decode a JWT. Returns payload dict or None if invalid/expired."""
    try:
        return jwt.decode(token, _secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        logger.debug("JWT expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"JWT invalid: {e}")
        return None


# ── Route decorator ───────────────────────────────────────────────────────────

def require_auth(f):
    """
    Decorator: protect a route with JWT bearer auth.
    Reads 'Authorization: Bearer <token>' and injects user_id as kwarg.

    Usage:
        @app.route('/api/protected')
        @require_auth
        def my_route(user_id):
            ...
    """
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or not Bearer."}), 401
        payload = decode_token(auth_header[7:])
        if not payload:
            return jsonify({"error": "Token is invalid or expired. Please sign in again."}), 401
        user_id = payload.get("user_id")
        if not user_id:
            return jsonify({"error": "Token missing user_id claim."}), 401
        return f(*args, user_id=user_id, **kwargs)
    return wrapped
