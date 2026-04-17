"""routes/retrain.py — Trigger Rasa model retraining via subprocess."""

import subprocess
import threading
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from config import RASA_PROJECT_DIR, RASA_VENV

retrain_bp = Blueprint("retrain", __name__)

# Simple state tracker (in-memory — good enough for single admin use)
_retrain_status = {"running": False, "log": "", "error": ""}


def _run_training():
    """Runs in a background thread so the API response is immediate."""
    global _retrain_status
    _retrain_status = {"running": True, "log": "", "error": ""}
    try:
        # Step 1: Write MySQL data → YAML files
        from nlu_sync import write_training_yaml, write_faq_yaml
        write_training_yaml()   # → data/nlu_admin.yml
        write_faq_yaml()        # → data/nlu_faq.yml + domain_faq.yml + data/rules_faq.yml
        _retrain_status["log"] = "YAML files written from MySQL.\n"

        # Step 2: Run rasa train
        cmd = (
            f'cmd /c "cd /d {RASA_PROJECT_DIR} && '
            f'{RASA_VENV} && rasa train --domain domain"'
        )
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=600
        )
        _retrain_status["log"]    += result.stdout + result.stderr
        _retrain_status["running"] = False
        if result.returncode != 0:
            _retrain_status["error"] = "Training failed. Check logs."
    except subprocess.TimeoutExpired:
        _retrain_status["running"] = False
        _retrain_status["error"]   = "Training timed out after 10 minutes."
    except Exception as e:
        _retrain_status["running"] = False
        _retrain_status["error"]   = str(e)



@retrain_bp.route("/api/retrain", methods=["POST"])
@jwt_required()
def trigger_retrain():
    if _retrain_status.get("running"):
        return jsonify({"message": "Training is already in progress.", "running": True}), 409

    thread = threading.Thread(target=_run_training, daemon=True)
    thread.start()
    return jsonify({"message": "Retraining started. Check /api/retrain/status for progress.", "running": True})


@retrain_bp.route("/api/retrain/status", methods=["GET"])
@jwt_required()
def retrain_status():
    return jsonify(_retrain_status)
