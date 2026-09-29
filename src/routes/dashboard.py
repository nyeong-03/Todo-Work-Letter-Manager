from datetime import date, timedelta

from flask import Blueprint, render_template

from src.db import get_db
from src.gmail_auth import load_account

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    db = get_db()
    today = date.today().isoformat()
    soon = (date.today() + timedelta(days=14)).isoformat()

    today_schedules = db.execute(
        "SELECT * FROM schedules WHERE date = ? AND status != '완료' ORDER BY title",
        (today,),
    ).fetchall()
    today_newsletters = db.execute(
        "SELECT * FROM newsletters WHERE received_date = ? ORDER BY id DESC",
        (today,),
    ).fetchall()

    upcoming_deadlines = db.execute(
        """SELECT * FROM schedules
           WHERE status != '완료' AND date IS NOT NULL AND date BETWEEN ? AND ?
           ORDER BY date ASC LIMIT 8""",
        (today, soon),
    ).fetchall()

    recent_newsletters = db.execute(
        "SELECT * FROM newsletters ORDER BY id DESC LIMIT 5"
    ).fetchall()

    goals = db.execute("SELECT * FROM goals ORDER BY target_date IS NULL, target_date ASC").fetchall()
    goal_progress = []
    for goal in goals:
        total = db.execute(
            "SELECT COUNT(*) FROM schedules WHERE goal_id = ?", (goal["id"],)
        ).fetchone()[0]
        done = db.execute(
            "SELECT COUNT(*) FROM schedules WHERE goal_id = ? AND status = '완료'", (goal["id"],)
        ).fetchone()[0]
        goal_progress.append({"goal": goal, "total": total, "done": done})

    gmail_account = load_account(db)

    return render_template(
        "dashboard.html",
        today_schedules=today_schedules,
        today_newsletters=today_newsletters,
        upcoming_deadlines=upcoming_deadlines,
        recent_newsletters=recent_newsletters,
        goal_progress=goal_progress,
        gmail_account=gmail_account,
        today=today,
    )
