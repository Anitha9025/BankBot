"""
app.py — Flask entry point for the BankBot Admin Panel backend.

Run with:
    python app.py
Server starts on http://localhost:8000
"""

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import JWT_SECRET_KEY

# ── Import route blueprints ────────────────────────────
from routes.auth     import auth_bp
from routes.logs     import logs_bp
from routes.faqs     import faqs_bp
from routes.training import training_bp
from routes.dashboard import dashboard_bp
from routes.retrain  import retrain_bp
from routes.chat     import chat_bp

# ── Create Flask app ───────────────────────────────────
app = Flask(__name__)
app.config["JWT_SECRET_KEY"]             = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"]   = 86400   # 24 hours
app.config["JWT_TOKEN_LOCATION"]         = ["headers", "query_string"]
app.config["JWT_QUERY_STRING_NAME"]      = "token"   # ?token=<jwt> for file downloads

# ── Enable CORS (allow React admin UI on :5174 and Chat UI on :5173) ────────
CORS(app, resources={r"/*": {"origins": ["http://localhost:5174", "http://127.0.0.1:5174", "http://localhost:5173", "http://127.0.0.1:5173"]}})

# ── JWT setup ──────────────────────────────────────────
JWTManager(app)


# ── Register blueprints ────────────────────────────────
app.register_blueprint(auth_bp)
app.register_blueprint(logs_bp)
app.register_blueprint(faqs_bp)
app.register_blueprint(training_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(retrain_bp)
app.register_blueprint(chat_bp)

# ── Sync NLU YAML → MySQL on first startup ─────────────────────────
with app.app_context():
    try:
        from nlu_sync import import_all_to_db
        import_all_to_db()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[startup] nlu_sync import failed: {e}")



@app.route("/health", methods=["GET"])
def health():
    """Quick health check endpoint."""
    return {"status": "ok", "service": "BankBot Admin API"}, 200


if __name__ == "__main__":
    print("=" * 50)
    print("  BankBot Admin Panel API")
    print("  Running on http://localhost:8000")
    print("  Default login: admin / admin123")
    print("=" * 50)
    app.run(host="0.0.0.0", port=8000, debug=True)
