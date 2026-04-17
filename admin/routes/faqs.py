"""routes/faqs.py — Full CRUD for FAQ table."""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from database import query, execute

faqs_bp = Blueprint("faqs", __name__)


@faqs_bp.route("/api/faqs", methods=["GET"])
@jwt_required()
def get_faqs():
    rows = query("SELECT * FROM faq ORDER BY id DESC")
    for r in rows:
        if r.get("created_at"): r["created_at"] = str(r["created_at"])
        if r.get("updated_at"): r["updated_at"] = str(r["updated_at"])
    return jsonify({"faqs": rows})


@faqs_bp.route("/api/faqs", methods=["POST"])
@jwt_required()
def create_faq():
    data     = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    answer   = (data.get("answer")   or "").strip()
    if not question or not answer:
        return jsonify({"error": "Question and answer are required."}), 400
    new_id = execute("INSERT INTO faq (question, answer) VALUES (%s, %s)", (question, answer))
    return jsonify({"id": new_id, "message": "FAQ created."}), 201


@faqs_bp.route("/api/faqs/<int:faq_id>", methods=["PUT"])
@jwt_required()
def update_faq(faq_id):
    data     = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    answer   = (data.get("answer")   or "").strip()
    if not question or not answer:
        return jsonify({"error": "Question and answer are required."}), 400
    execute("UPDATE faq SET question=%s, answer=%s WHERE id=%s", (question, answer, faq_id))
    return jsonify({"message": "FAQ updated."})


@faqs_bp.route("/api/faqs/<int:faq_id>", methods=["DELETE"])
@jwt_required()
def delete_faq(faq_id):
    execute("DELETE FROM faq WHERE id=%s", (faq_id,))
    return jsonify({"message": "FAQ deleted."})
