
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).with_name("learning_coach.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                goal TEXT,
                current_level TEXT,
                duration_days INTEGER,
                daily_minutes INTEGER,
                plan_json TEXT,
                created_at TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER,
                topic TEXT,
                score INTEGER,
                total INTEGER,
                answers_json TEXT,
                weak_topics_json TEXT,
                created_at TEXT
            )
        """)


def save_plan(
    subject, goal, level, duration, daily_minutes, plan
):
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO plans
            (subject, goal, current_level, duration_days,
             daily_minutes, plan_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            subject,
            goal,
            level,
            duration,
            daily_minutes,
            json.dumps(plan),
            datetime.now().isoformat(timespec="seconds")
        ))

        return cursor.lastrowid


def get_plan(plan_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM plans WHERE id = ?",
            (plan_id,)
        ).fetchone()

        if row is None:
            return None

        result = dict(row)
        result["plan"] = json.loads(result.pop("plan_json"))
        return result


def list_plans(limit=20):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, subject, goal, current_level,
                   duration_days, daily_minutes, created_at
            FROM plans ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]


def save_attempt(
    plan_id, topic, score, total, answers, weak_topics
):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO quiz_attempts
            (plan_id, topic, score, total, answers_json,
             weak_topics_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            plan_id,
            topic,
            score,
            total,
            json.dumps(answers),
            json.dumps(weak_topics),
            datetime.now().isoformat(timespec="seconds")
        ))


def list_attempts(limit=50):
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM quiz_attempts
            ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()

        results = []

        for row in rows:
            item = dict(row)
            item["answers"] = json.loads(
                item.pop("answers_json")
            )
            item["weak_topics"] = json.loads(
                item.pop("weak_topics_json")
            )
            results.append(item)

        return results
