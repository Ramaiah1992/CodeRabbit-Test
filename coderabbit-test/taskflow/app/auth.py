import base64
import hashlib
import hmac
import json
import secrets
import time
from functools import wraps

from flask import current_app, g, jsonify, request

PBKDF2_ROUNDS = 240_000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Return a self-describing PBKDF2 hash: algorithm$rounds$salt$digest."""
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ROUNDS)
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = encoded.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), int(rounds)
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


def _sign(body: str) -> str:
    key = current_app.config["SECRET_KEY"].encode()
    return hmac.new(key, body.encode(), hashlib.sha256).hexdigest()


def issue_token(user_id: int) -> str:
    payload = {
        "sub": user_id,
        "exp": int(time.time()) + current_app.config["TOKEN_TTL_SECONDS"],
    }
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    return f"{body}.{_sign(body)}"


def read_token(token: str):
    """Return the user id encoded in a valid token, or None."""
    try:
        body, signature = token.split(".")
    except ValueError:
        return None

    if not hmac.compare_digest(_sign(body), signature):
        return None

    padding = "=" * (-len(body) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(body + padding))
    except (ValueError, json.JSONDecodeError):
        return None

    if payload.get("exp", 0) < time.time():
        return None
    return payload.get("sub")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify(error="missing bearer token"), 401

        user_id = read_token(header[len("Bearer ") :])
        if user_id is None:
            return jsonify(error="invalid or expired token"), 401

        g.user_id = user_id
        return view(*args, **kwargs)

    return wrapped
