from __future__ import annotations

import sqlite3
from datetime import date, timedelta
from typing import Dict, List

from flask import Flask, jsonify, render_template, request

app = Flask(__name__, template_folder=".", static_folder=".", static_url_path="")
DATABASE = "study_tracker.db"


def get_db_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                minutes INTEGER NOT NULL DEFAULT 0,
                score INTEGER NOT NULL DEFAULT 0,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_plan (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                focus TEXT NOT NULL,
                task TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def today() -> str:
    return date.today().isoformat()


def get_dashboard_stats() -> Dict[str, object]:
    current_date = today()
    with get_db_connection() as connection:
        sessions = connection.execute(
            "SELECT * FROM study_sessions WHERE date = ? ORDER BY created_at DESC",
            (current_date,),
        ).fetchall()
        plans = connection.execute(
            "SELECT * FROM daily_plan WHERE date = ? ORDER BY id DESC",
            (current_date,),
        ).fetchall()

        categories = ["grammar", "vocabulary", "kanji", "dokkai"]
        category_totals = {
            category: sum(
                int(item["minutes"]) for item in sessions if item["category"] == category
            )
            for category in categories
        }
        total_minutes = sum(int(item["minutes"]) for item in sessions)
        total_sessions = len(sessions)
        total_score = sum(int(item["score"]) for item in sessions)
        top_category = max(category_totals, key=category_totals.get) if total_minutes else "Ready to begin"
        weekly_activity = []
        for days_ago in range(6, -1, -1):
            activity_date = date.today() - timedelta(days=days_ago)
            activity_key = activity_date.isoformat()
            activity_minutes = connection.execute(
                "SELECT COALESCE(SUM(minutes), 0) FROM study_sessions WHERE date = ?",
                (activity_key,),
            ).fetchone()[0]
            weekly_activity.append({
                "date": activity_key,
                "label": activity_date.strftime("%a"),
                "minutes": int(activity_minutes),
            })

        completed_plan_count = sum(1 for item in plans if item["completed"])
        plan_total = len(plans)
        completion_percent = round((completed_plan_count / plan_total) * 100, 1) if plan_total else 0

        streak = 0
        cursor = date.today()
        while True:
            day_key = cursor.isoformat()
            day_count = connection.execute(
                "SELECT COUNT(*) FROM study_sessions WHERE date = ?",
                (day_key,),
            ).fetchone()[0]
            if day_count > 0:
                streak += 1
                cursor -= timedelta(days=1)
            else:
                break

        return {
            "today_date": current_date,
            "sessions": [dict(item) for item in sessions],
            "plans": [dict(item) for item in plans],
            "total_minutes": total_minutes,
            "total_sessions": total_sessions,
            "total_score": total_score,
            "completed_plan_count": completed_plan_count,
            "plan_total": plan_total,
            "completion_percent": completion_percent,
            "streak": streak,
            "category_totals": category_totals,
            "top_category": top_category,
            "weekly_activity": weekly_activity,
        }


@app.route("/")
def index():
    stats = get_dashboard_stats()
    return render_template("index.html", stats=stats)


@app.route("/api/dashboard")
def api_dashboard():
    return jsonify(get_dashboard_stats())


@app.route("/add_session", methods=["POST"])
def add_session():
    category = request.form.get("category", "grammar").strip().lower()
    title = request.form.get("title", "Study session").strip()
    minutes = int(request.form.get("minutes", 0) or 0)
    score = int(request.form.get("score", 0) or 0)
    notes = request.form.get("notes", "").strip()

    if not title:
        return "Title is required", 400

    with get_db_connection() as connection:
        connection.execute(
            "INSERT INTO study_sessions (date, category, title, minutes, score, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (today(), category, title, minutes, score, notes),
        )
        connection.commit()

    return "Study session added", 200


@app.route("/save_plan", methods=["POST"])
def save_plan():
    focus = request.form.get("focus", "Daily study").strip()
    task = request.form.get("task", "").strip()

    if not task:
        return "Plan task is required", 400

    with get_db_connection() as connection:
        connection.execute(
            "INSERT INTO daily_plan (date, focus, task, completed) VALUES (?, ?, ?, 0)",
            (today(), focus, task),
        )
        connection.commit()

    return "Plan saved", 200


@app.route("/toggle_plan/<int:plan_id>", methods=["POST"])
def toggle_plan(plan_id: int):
    with get_db_connection() as connection:
        plan = connection.execute(
            "SELECT completed FROM daily_plan WHERE id = ?",
            (plan_id,),
        ).fetchone()
        if not plan:
            return "Plan not found", 404

        new_value = 0 if plan["completed"] else 1
        connection.execute(
            "UPDATE daily_plan SET completed = ? WHERE id = ?",
            (new_value, plan_id),
        )
        connection.commit()

    return "Plan updated", 200


@app.route("/reset", methods=["POST"])
def reset_data():
    with get_db_connection() as connection:
        connection.execute("DELETE FROM study_sessions")
        connection.execute("DELETE FROM daily_plan")
        connection.commit()
    return "All data cleared", 200


init_db()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
