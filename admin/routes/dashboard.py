"""routes/dashboard.py — Dashboard stats and intent analytics."""

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from database import query

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard():
    total_queries = query("SELECT COUNT(*) AS cnt FROM user_logs")[0]["cnt"]

    # Success = logs where confidence > 0.7
    success_rows  = query("SELECT COUNT(*) AS cnt FROM user_logs WHERE confidence > 0.7")[0]["cnt"]
    success_rate  = round((success_rows / total_queries * 100), 1) if total_queries > 0 else 0

    # Count distinct intents in user_logs
    intent_count  = query("SELECT COUNT(DISTINCT intent) AS cnt FROM user_logs WHERE intent IS NOT NULL")[0]["cnt"]

    # Average confidence
    avg_conf_row  = query("SELECT AVG(confidence) AS avg_c FROM user_logs WHERE confidence IS NOT NULL")[0]
    avg_confidence = round(avg_conf_row["avg_c"] or 0, 3)

    # Total FAQs and Training examples
    total_faqs     = query("SELECT COUNT(*) AS cnt FROM faq")[0]["cnt"]
    total_training = query("SELECT COUNT(*) AS cnt FROM training_data")[0]["cnt"]

    return jsonify({
        "total_queries":    total_queries,
        "success_rate":     success_rate,
        "intent_count":     intent_count,
        "avg_confidence":   avg_confidence,
        "total_faqs":       total_faqs,
        "total_training":   total_training,
    })


@dashboard_bp.route("/api/analytics", methods=["GET"])
@jwt_required()
def get_analytics():
    # Top intents by frequency
    intent_freq = query("""
        SELECT intent, COUNT(*) AS count
        FROM user_logs
        WHERE intent IS NOT NULL AND intent != ''
        GROUP BY intent
        ORDER BY count DESC
        LIMIT 10
    """)

    # Daily query volume (last 14 days)
    daily_volume = query("""
        SELECT DATE(timestamp) AS date, COUNT(*) AS count
        FROM user_logs
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 14 DAY)
        GROUP BY DATE(timestamp)
        ORDER BY date ASC
    """)
    for r in daily_volume:
        if r.get("date"):
            r["date"] = str(r["date"])

    # Avg confidence per intent
    confidence_by_intent = query("""
        SELECT intent, ROUND(AVG(confidence), 3) AS avg_confidence
        FROM user_logs
        WHERE intent IS NOT NULL AND confidence IS NOT NULL
        GROUP BY intent
        ORDER BY avg_confidence DESC
        LIMIT 10
    """)

    return jsonify({
        "intent_frequency":     intent_freq,
        "daily_volume":         daily_volume,
        "confidence_by_intent": confidence_by_intent,
    })
