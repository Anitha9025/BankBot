"""routes/training.py — Full CRUD for training_data table."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from database import query, execute

training_bp = Blueprint("training", __name__)


@training_bp.route("/api/training", methods=["GET"])
@jwt_required()
def get_training():
    rows = query("SELECT * FROM training_data ORDER BY intent, id")
    for r in rows:
        if r.get("created_at"): r["created_at"] = str(r["created_at"])
        if r.get("updated_at"): r["updated_at"] = str(r["updated_at"])
    return jsonify({"training_data": rows})


@training_bp.route("/api/training", methods=["POST"])
@jwt_required()
def create_training():
    data         = request.get_json(silent=True) or {}
    intent       = (data.get("intent")       or "").strip()
    example_text = (data.get("example_text") or "").strip()
    if not intent or not example_text:
        return jsonify({"error": "Intent and example_text are required."}), 400
    new_id = execute(
        "INSERT INTO training_data (intent, example_text) VALUES (%s, %s)",
        (intent, example_text)
    )
    return jsonify({"id": new_id, "message": "Training example added."}), 201


@training_bp.route("/api/training/<int:row_id>", methods=["PUT"])
@jwt_required()
def update_training(row_id):
    data         = request.get_json(silent=True) or {}
    intent       = (data.get("intent")       or "").strip()
    example_text = (data.get("example_text") or "").strip()
    if not intent or not example_text:
        return jsonify({"error": "Intent and example_text are required."}), 400
    execute(
        "UPDATE training_data SET intent=%s, example_text=%s WHERE id=%s",
        (intent, example_text, row_id)
    )
    return jsonify({"message": "Training example updated."})


@training_bp.route("/api/training/<int:row_id>", methods=["DELETE"])
@jwt_required()
def delete_training(row_id):
    execute("DELETE FROM training_data WHERE id=%s", (row_id,))
    return jsonify({"message": "Training example deleted."})
