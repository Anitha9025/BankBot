"""
reset_admin.py — Run once to set the correct admin password hash in MySQL.
Usage: python reset_admin.py
"""

import bcrypt
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

# Generate bcrypt hash for "admin123"
password   = b"admin123"
hashed     = bcrypt.hashpw(password, bcrypt.gensalt()).decode("utf-8")

print(f"Generated hash: {hashed}")

# Connect to MySQL and update/insert admin user
conn = pymysql.connect(
    host     = os.getenv("DB_HOST", "localhost"),
    port     = int(os.getenv("DB_PORT", 3306)),
    user     = os.getenv("DB_USER", "root"),
    password = os.getenv("DB_PASSWORD", ""),
    database = os.getenv("DB_NAME", "bankbot_admin"),
    charset  = "utf8mb4",
)

with conn.cursor() as cursor:
    # Delete old admin row and insert fresh one with correct hash
    cursor.execute("DELETE FROM admin_users WHERE username = 'admin'")
    cursor.execute(
        "INSERT INTO admin_users (username, password_hash) VALUES (%s, %s)",
        ("admin", hashed)
    )
conn.commit()
conn.close()

print("✅ Admin password reset to: admin / admin123")
print("   You can now log in at http://localhost:5174")
