import sqlite3

from flask import Blueprint, current_app, jsonify, request

from app.auth import hash_password, issue_token, verify_password
from app.db import get_connection
from app.models import User

bp = Blueprint("users", __name__, url_prefix="/api/users")


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or "@" not in email:
        return jsonify(error="a valid email address is required"), 400

    minimum = current_app.config["MIN_PASSWORD_LENGTH"]
    if len(password) < minimum:
        return jsonify(error=f"password must be at least {minimum} characters"), 400

    try:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, hash_password(password)),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        return jsonify(error="email already registered"), 409

    return jsonify(id=user_id, email=email), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, email, password_hash, created_at FROM users WHERE email = ?",
            (email,),
        ).fetchone()

    if row is None or not verify_password(password, row["password_hash"]):
        return jsonify(error="invalid credentials"), 401

    return jsonify(token=issue_token(row["id"]), user=User.from_row(row).to_dict())
