"""routes/logs.py — User query logs: list (paginated) + CSV export."""

import csv
import io
from flask import Blueprint, jsonify, request, Response
from flask_jwt_extended import jwt_required
from database import query

logs_bp = Blueprint("logs", __name__)


@logs_bp.route("/api/logs", methods=["GET"])
@jwt_required()
def get_logs():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    offset   = (page - 1) * per_page

    rows  = query(
        "SELECT * FROM user_logs ORDER BY timestamp DESC LIMIT %s OFFSET %s",
        (per_page, offset)
    )
    total = query("SELECT COUNT(*) AS cnt FROM user_logs")[0]["cnt"]

    # Convert datetime objects to strings for JSON serialisation
    for r in rows:
        if r.get("timestamp"):
            r["timestamp"] = str(r["timestamp"])

    return jsonify({"logs": rows, "total": total, "page": page, "per_page": per_page})


@logs_bp.route("/api/logs/export", methods=["GET"])
@jwt_required()
def export_logs():
    rows = query("SELECT id, message, intent, confidence, response, timestamp FROM user_logs ORDER BY timestamp DESC")

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Message", "Intent", "Confidence", "Response", "Timestamp"])
    for r in rows:
        writer.writerow([r["id"], r["message"], r["intent"], r["confidence"], r["response"], r["timestamp"]])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=user_logs.csv"}
    )
