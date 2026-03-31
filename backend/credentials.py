"""
Encrypt / decrypt AWS credentials stored in the database.
Uses Fernet symmetric encryption derived from SECRET_KEY.
"""
import os
import base64
import hashlib
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()


def _fernet() -> Fernet:
    raw = os.getenv("SECRET_KEY", "cloudproof-dev-secret-change-in-production")
    # Derive a 32-byte key from whatever string is in SECRET_KEY
    key_bytes = hashlib.sha256(raw.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key_bytes))


def encrypt_credential(plain: str) -> str:
    """Encrypt a plaintext credential string. Returns a base64 ciphertext string."""
    if not plain:
        return ""
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_credential(cipher: str) -> str:
    """Decrypt a stored ciphertext string. Returns plaintext."""
    if not cipher:
        return ""
    return _fernet().decrypt(cipher.encode()).decode()
