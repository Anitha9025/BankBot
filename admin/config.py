import os
from dotenv import load_dotenv

load_dotenv()

# ── MySQL ──────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME",     "bankbot_admin"),
    "charset":  "utf8mb4",
    "cursorclass": "DictCursor",   # returns rows as dicts
}

# ── JWT ────────────────────────────────────────────────
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")

# ── Rasa ───────────────────────────────────────────────
RASA_PROJECT_DIR = os.getenv("RASA_PROJECT_DIR", r"e:\BankBot")
RASA_VENV        = os.getenv("RASA_VENV",        r"e:\BankBot\banking_env\Scripts\activate")
