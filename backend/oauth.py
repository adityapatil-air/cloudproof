"""
GitHub and Google OAuth2 helpers.

Flow per provider:
  1.  frontend hits  GET /api/auth/<provider>          → backend redirects browser to provider
  2.  provider redirects back to               GET /api/auth/<provider>/callback?code=…&state=…
  3.  backend exchanges code → access_token → user_profile
  4.  backend upserts user, mints JWT, redirects frontend to /auth/callback?token=…
"""

import os
import secrets
import logging
import requests
import jwt
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


# ── helpers ──────────────────────────────────────────────────────────────────

def _backend_url() -> str:
    """Always read fresh from env so Render env-vars are honoured at runtime."""
    return os.getenv('BACKEND_URL', 'http://localhost:5000').rstrip('/')

def _frontend_url() -> str:
    return os.getenv('FRONTEND_URL', 'http://localhost:3000').rstrip('/')

def _github_client_id() -> str:
    return os.getenv('GITHUB_CLIENT_ID', '')

def _github_client_secret() -> str:
    return os.getenv('GITHUB_CLIENT_SECRET', '')

def _google_client_id() -> str:
    return os.getenv('GOOGLE_CLIENT_ID', '')

def _google_client_secret() -> str:
    return os.getenv('GOOGLE_CLIENT_SECRET', '')


# ── CSRF state (signed JWT, 10-min TTL) ─────────────────────────────────────

def generate_state(provider: str) -> str:
    """Create a short-lived signed state token to prevent CSRF."""
    payload = {
        'provider': provider,
        'nonce':    secrets.token_hex(16),
        'exp':      datetime.now(timezone.utc) + timedelta(minutes=10),
    }
    return jwt.encode(payload, os.getenv('SECRET_KEY', 'dev-secret'), algorithm='HS256')


def verify_state(state: str, expected_provider: str) -> bool:
    try:
        payload = jwt.decode(state, os.getenv('SECRET_KEY', 'dev-secret'), algorithms=['HS256'])
        return payload.get('provider') == expected_provider
    except Exception:
        return False


# ── GitHub ───────────────────────────────────────────────────────────────────

def github_auth_url(state: str) -> str:
    cb = f"{_backend_url()}/api/auth/github/callback"
    logger.info(f"[GitHub OAuth] redirect_uri = {cb}")
    return (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={_github_client_id()}"
        f"&redirect_uri={cb}"
        f"&scope=user:email"
        f"&state={state}"
    )


def github_get_user(code: str) -> dict:
    """Exchange authorization code for GitHub user profile."""
    cb = f"{_backend_url()}/api/auth/github/callback"
    logger.info(f"[GitHub OAuth] token exchange redirect_uri = {cb}")

    token_res = requests.post(
        'https://github.com/login/oauth/access_token',
        json={
            'client_id':     _github_client_id(),
            'client_secret': _github_client_secret(),
            'code':          code,
            'redirect_uri':  cb,
        },
        headers={'Accept': 'application/json'},
        timeout=15,
    )
    token_res.raise_for_status()
    token_data = token_res.json()
    access_token = token_data.get('access_token')
    if not access_token:
        raise ValueError(f"GitHub token exchange failed: {token_data}")

    hdrs = {'Authorization': f'token {access_token}', 'Accept': 'application/json'}

    user_data = requests.get('https://api.github.com/user', headers=hdrs, timeout=10).json()

    # Public email may be None — fetch verified primary separately
    email = user_data.get('email')
    if not email:
        emails = requests.get('https://api.github.com/user/emails', headers=hdrs, timeout=10).json()
        primary = next((e for e in emails if e.get('primary') and e.get('verified')), None)
        email = primary['email'] if primary else None

    return {
        'oauth_id':       str(user_data['id']),
        'email':          email,
        'name':           user_data.get('name') or user_data.get('login', ''),
        'username_hint':  user_data.get('login', '').lower(),
        'avatar':         user_data.get('avatar_url'),
        'email_verified': True,     # GitHub only exposes verified emails
    }


# ── Google ───────────────────────────────────────────────────────────────────

def google_auth_url(state: str) -> str:
    cb = f"{_backend_url()}/api/auth/google/callback"
    logger.info(f"[Google OAuth] redirect_uri = {cb}")
    return (
        f"https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={_google_client_id()}"
        f"&redirect_uri={cb}"
        f"&response_type=code"
        f"&scope=openid+email+profile"
        f"&state={state}"
        f"&access_type=offline"
        f"&prompt=select_account"
    )


def google_get_user(code: str) -> dict:
    """Exchange authorization code for Google user profile."""
    cb = f"{_backend_url()}/api/auth/google/callback"
    logger.info(f"[Google OAuth] token exchange redirect_uri = {cb}")

    token_res = requests.post(
        'https://oauth2.googleapis.com/token',
        data={
            'code':          code,
            'client_id':     _google_client_id(),
            'client_secret': _google_client_secret(),
            'redirect_uri':  cb,
            'grant_type':    'authorization_code',
        },
        timeout=15,
    )
    token_res.raise_for_status()
    token_data = token_res.json()
    access_token = token_data.get('access_token')
    if not access_token:
        raise ValueError(f"Google token exchange failed: {token_data}")

    userinfo = requests.get(
        'https://www.googleapis.com/oauth2/v3/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=10,
    ).json()

    email = userinfo.get('email', '')
    # Build a sensible username from email local-part
    username_hint = email.split('@')[0].lower().replace('.', '_').replace('+', '_') if email else 'user'

    return {
        'oauth_id':       userinfo.get('sub', ''),
        'email':          email,
        'name':           userinfo.get('name', ''),
        'username_hint':  username_hint,
        'avatar':         userinfo.get('picture'),
        'email_verified': userinfo.get('email_verified', False),
    }
