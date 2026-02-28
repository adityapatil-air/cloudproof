"""
Secure storage and retrieval of AWS credentials.
Uses Fernet symmetric encryption. Requires CREDENTIALS_ENCRYPTION_KEY in .env.
"""
import os
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


def _get_fernet_key():
    """Derive or use a 32-byte key for Fernet encryption."""
    key = os.getenv("CREDENTIALS_ENCRYPTION_KEY")
    if key:
        if len(key) < 32:
            # Derive 32 bytes from the provided secret
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"cloudproof_credentials",
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(
                kdf.derive(key.encode() if isinstance(key, str) else key)
            ).decode()
        elif len(key) == 44 and key.endswith("="):
            pass  # Already Fernet key
        else:
            key = base64.urlsafe_b64encode(
                (key[:32] if len(key) > 32 else key.ljust(32)).encode()
            ).decode()
        return key.encode()
    # Fallback: derive from a default (NOT for production)
    default_secret = os.getenv("SECRET_KEY", "cloudproof-dev-secret-change-me")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"cloudproof_credentials",
        iterations=100000,
    )
    return base64.urlsafe_b64encode(
        kdf.derive(default_secret.encode())
    )


def encrypt_credential(plain: str) -> str | None:
    """Encrypt a credential string. Returns base64 ciphertext or None if empty."""
    if not plain or not plain.strip():
        return None
    try:
        f = Fernet(_get_fernet_key())
        return f.encrypt(plain.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise


def decrypt_credential(cipher: str | None) -> str | None:
    """Decrypt a credential. Returns plaintext or None."""
    if not cipher or not cipher.strip():
        return None
    try:
        f = Fernet(_get_fernet_key())
        return f.decrypt(cipher.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise
