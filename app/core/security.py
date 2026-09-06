import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional, Dict, Any

from app.core.config import settings

# Salted PBKDF2 Password Hashing
def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a secure random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${key.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored salt$hash."""
    try:
        salt, key_hex = stored_hash.split('$', 1)
        expected_key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return hmac.compare_digest(expected_key.hex(), key_hex)
    except Exception:
        return False

# HMAC-SHA256 Signed Session Tokens
def _base64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _base64_url_decode(data_str: str) -> bytes:
    padding = '=' * (-len(data_str) % 4)
    return base64.urlsafe_b64decode((data_str + padding).encode('utf-8'))

def create_session_token(user_id: int, username: str, role: str, max_age_days: int = 30) -> str:
    """Create a cryptographically signed session token containing user claims."""
    payload = {
        "uid": user_id,
        "usr": username,
        "role": role,
        "exp": int(time.time()) + (max_age_days * 86400)
    }
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    payload_b64 = _base64_url_encode(payload_json)
    
    signature = hmac.new(
        settings.SECRET_KEY.encode('utf-8'),
        payload_b64.encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = _base64_url_encode(signature)
    
    return f"{payload_b64}.{sig_b64}"

def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify token signature and expiration, returns claims dictionary or None."""
    if not token or '.' not in token:
        return None
    try:
        payload_b64, sig_b64 = token.split('.', 1)
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            payload_b64.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        provided_sig = _base64_url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, provided_sig):
            return None
        
        payload_bytes = _base64_url_decode(payload_b64)
        claims = json.loads(payload_bytes.decode('utf-8'))
        
        # Check expiration
        if claims.get("exp", 0) < int(time.time()):
            return None
        
        return claims
    except Exception:
        return None
