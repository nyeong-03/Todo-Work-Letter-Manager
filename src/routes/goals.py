from flask import Blueprint, redirect, render_template, request, url_for

from src.db import get_db

bp = Blueprint("goals", __name__, url_prefix="/goals")


@bp.route("/")
def index():
    db = get_db()
    goals = db.execute(
        "SELECT * FROM goals ORDER BY target_date IS NULL, target_date ASC"
    ).fetchall()

    goals_with_counts = []
    for goal in goals:
        newsletter_count = db.execute(
            "SELECT COUNT(*) FROM newsletters WHERE goal_id = ?", (goal["id"],)
        ).fetchone()[0]
        schedule_total = db.execute(
            "SELECT COUNT(*) FROM schedules WHERE goal_id = ?", (goal["id"],)
        ).fetchone()[0]
        schedule_done = db.execute(
            "SELECT COUNT(*) FROM schedules WHERE goal_id = ? AND status = '완료'", (goal["id"],)
        ).fetchone()[0]
        goals_with_counts.append(
            {
                "goal": goal,
                "newsletter_count": newsletter_count,
                "schedule_total": schedule_total,
                "schedule_done": schedule_done,
            }
        )

    return render_template("goals.html", goals=goals_with_counts)


@bp.route("/add", methods=["POST"])
def add():
    db = get_db()
    title = request.form.get("title", "").strip()
    field = request.form.get("field", "").strip() or None
    target_date = request.form.get("target_date") or None
    memo = request.form.get("memo", "").strip() or None

    if not title:
        return redirect(url_for("goals.index"))

    db.execute(
        "INSERT INTO goals (title, field, target_date, memo) VALUES (?, ?, ?, ?)",
        (title, field, target_date, memo),
    )
    db.commit()
    return redirect(url_for("goals.index"))


@bp.route("/<int:goal_id>/update", methods=["POST"])
def update(goal_id: int):
    db = get_db()
    title = request.form.get("title", "").strip()
    field = request.form.get("field", "").strip() or None
    target_date = request.form.get("target_date") or None
    memo = request.form.get("memo", "").strip() or None

    if not title:
        return redirect(url_for("goals.index"))

    db.execute(
        "UPDATE goals SET title = ?, field = ?, target_date = ?, memo = ? WHERE id = ?",
        (title, field, target_date, memo, goal_id),
    )
    db.commit()
    return redirect(url_for("goals.index"))


@bp.route("/<int:goal_id>/delete", methods=["POST"])
def delete(goal_id: int):
    db = get_db()
    db.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    db.commit()
    return redirect(url_for("goals.index"))
