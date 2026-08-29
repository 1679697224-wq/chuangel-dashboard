"""PBKDF2 密码验证与可撤销会话。"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Dict, Optional, Tuple


PBKDF2_ITERATIONS = 310_000


def hash_password(password: str, salt: Optional[bytes] = None) -> str:
    actual_salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), actual_salt, PBKDF2_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(actual_salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_b64, digest_b64 = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_b64.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations)
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _b64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode((value + "=" * (-len(value) % 4)).encode("ascii"))


def issue_token(
    username: str, secret: str, ttl_seconds: int, session_id: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    now = int(time.time())
    payload = {
        "sub": username,
        "sid": session_id or secrets.token_urlsafe(24),
        "iat": now,
        "exp": now + ttl_seconds,
    }
    encoded = _b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _b64_encode(
        hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
    )
    return encoded + "." + signature, payload


def verify_token(token: str, secret: str) -> Optional[Dict[str, Any]]:
    try:
        encoded, supplied = token.split(".", 1)
        expected = _b64_encode(
            hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
        )
        if not hmac.compare_digest(expected, supplied):
            return None
        payload = json.loads(_b64_decode(encoded).decode("utf-8"))
        if int(payload.get("exp", 0)) <= int(time.time()):
            return None
        if not payload.get("sub") or not payload.get("sid"):
            return None
        return payload
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError):
        return None
