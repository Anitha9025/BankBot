"""routes/auth.py — Admin login + JWT token generation."""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
import bcrypt
from database import query

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data     = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    rows = query("SELECT * FROM admin_users WHERE username = %s", (username,))
    if not rows:
        return jsonify({"error": "Invalid credentials."}), 401

    user = rows[0]
    # bcrypt.checkpw compares plain password with stored hash
    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return jsonify({"error": "Invalid credentials."}), 401

    token = create_access_token(identity=username)
    return jsonify({"token": token, "username": username}), 200
