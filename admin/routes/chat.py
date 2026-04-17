"""routes/chat.py — Proxies chat to Rasa and logs user queries to MySQL."""

import requests
from flask import Blueprint, request, jsonify
from database import query, execute
import logging

chat_bp = Blueprint("chat", __name__)
logger = logging.getLogger(__name__)

RASA_WEBHOOK_URL = "http://localhost:5005/webhooks/rest/webhook"
RASA_TRACKER_URL = "http://localhost:5005/conversations/{sender_id}/tracker"

@chat_bp.route("/api/chat", methods=["POST"])
def proxy_chat():
    data = request.get_json(silent=True) or {}
    sender = data.get("sender")
    message = data.get("message")

    if not sender or not message:
        return jsonify({"error": "sender and message are required"}), 400

    # 1. Forward the message to Rasa
    try:
        res = requests.post(RASA_WEBHOOK_URL, json={"sender": sender, "message": message}, timeout=10)
        bot_responses = res.json()
    except Exception as e:
        logger.error(f"[proxy_chat] Error connecting to Rasa: {e}")
        return jsonify({"error": "Chatbot is temporarily unavailable"}), 503

    # concatenate all text responses into one string for logging
    response_text = " \\n ".join([resp.get("text", "") for resp in bot_responses if resp.get("text")])

    # 2. Get the intent and confidence from Rasa's Tracker
    intent_name = "unknown"
    confidence = 0.0
    try:
        tracker_res = requests.get(RASA_TRACKER_URL.format(sender_id=sender), timeout=5)
        tracker_data = tracker_res.json()
        latest_message = tracker_data.get("latest_message", {})
        intent_data = latest_message.get("intent", {})
        intent_name = intent_data.get("name") or "unknown"
        confidence = intent_data.get("confidence") or 0.0
    except Exception as e:
        logger.warning(f"[proxy_chat] Could not fetch tracker for logging: {e}")

    # 3. Log to MySQL user_logs
    try:
        execute(
            "INSERT INTO user_logs (message, intent, confidence, response) VALUES (%s, %s, %s, %s)",
            (message, intent_name, round(confidence, 4), response_text[:1000] if response_text else None)
        )
    except Exception as e:
        logger.warning(f"[proxy_chat] Could not write to MySQL: {e}")

    # 4. Return responses to the frontend
    return jsonify(bot_responses), 200
