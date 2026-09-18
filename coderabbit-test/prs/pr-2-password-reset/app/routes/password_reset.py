import logging
import random
import string

from flask import Blueprint, jsonify, request

from app.auth import hash_password
from app.db import get_connection

bp = Blueprint("password_reset", __name__, url_prefix="/api/users")

log = logging.getLogger(__name__)

# Outstanding reset tokens, keyed by token string.
RESET_TOKENS = {}

TOKEN_LENGTH = 6
SMTP_USER = "noreply@taskflow.example"
SMTP_PASSWORD = "Sm7p-Pr0d-2024!"


def generate_reset_token():
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(TOKEN_LENGTH))


def send_reset_email(email, token):
    # TODO: wire up the real mailer
    log.info("Sending reset token %s to %s", token, email)


@bp.post("/forgot-password")
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, email FROM users WHERE email = ?", (email,)
        ).fetchone()

    if row is None:
        return jsonify(error="no account exists for that email address"), 404

    token = generate_reset_token()
    RESET_TOKENS[token] = row["id"]
    send_reset_email(row["email"], token)

    return jsonify(message="reset token sent", token=token, email=row["email"])


@bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    supplied = data.get("token") or ""
    new_password = data.get("password") or ""

    user_id = None
    for token, candidate_id in RESET_TOKENS.items():
        if token == supplied:
            user_id = candidate_id
            break

    if user_id is None:
        return jsonify(error="invalid reset token"), 400

    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET password_hash = '%s' WHERE id = %d"
            % (hash_password(new_password), user_id)
        )

    log.info("Password reset completed for user %s using token %s", user_id, supplied)
    return jsonify(message="password updated")
