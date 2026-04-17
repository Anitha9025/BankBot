"""
database.py — MySQL connection helpers using PyMySQL.

Usage:
    rows = query("SELECT * FROM faq")
    execute("INSERT INTO faq (question, answer) VALUES (%s, %s)", (q, a))
"""

import pymysql
import pymysql.cursors
from config import DB_CONFIG


def get_connection():
    """Open and return a new MySQL connection."""
    cfg = dict(DB_CONFIG)
    cfg["cursorclass"] = pymysql.cursors.DictCursor   # rows as dicts
    return pymysql.connect(**cfg)


def query(sql: str, params: tuple = ()) -> list:
    """
    Run a SELECT and return all rows as a list of dicts.
    Example:
        rows = query("SELECT * FROM faq WHERE id = %s", (faq_id,))
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conn.close()


def execute(sql: str, params: tuple = ()) -> int:
    """
    Run INSERT / UPDATE / DELETE.
    Returns the last inserted row id (useful for INSERT).
    Example:
        new_id = execute("INSERT INTO faq (question, answer) VALUES (%s,%s)", (q, a))
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()
