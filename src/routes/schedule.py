from flask import Blueprint, redirect, render_template, request, url_for

from src.db import get_db

bp = Blueprint("schedule", __name__, url_prefix="/schedule")

SCHEDULE_TYPES = ["접수 마감", "시험일", "행사일", "준비 할 일", "일반 일정"]


@bp.route("/")
def index():
    db = get_db()
    schedules = db.execute(
        """SELECT schedules.*, goals.title AS goal_title
           FROM schedules
           LEFT JOIN goals ON goals.id = schedules.goal_id
           ORDER BY status = '완료', date IS NULL, date ASC"""
    ).fetchall()
    goals = db.execute("SELECT id, title FROM goals ORDER BY title").fetchall()

    # Pre-fill values coming from "뉴스레터 -> 일정으로 옮기기" (see newsletters.to_schedule)
    prefill = {
        "title": request.args.get("prefill_title", ""),
        "date": request.args.get("prefill_date", ""),
        "type": request.args.get("prefill_type", "일반 일정"),
        "goal_id": request.args.get("prefill_goal_id", ""),
        "newsletter_id": request.args.get("prefill_newsletter_id", ""),
        "source_note": request.args.get("prefill_source_note", ""),
    }

    return render_template(
        "schedule.html",
        schedules=schedules,
        goals=goals,
        schedule_types=SCHEDULE_TYPES,
        prefill=prefill,
    )


@bp.route("/add", methods=["POST"])
def add():
    db = get_db()
    title = request.form.get("title", "").strip()
    schedule_date = request.form.get("date") or None
    schedule_type = request.form.get("type") or "일반 일정"
    goal_id = request.form.get("goal_id") or None
    newsletter_id = request.form.get("newsletter_id") or None
    source_note = request.form.get("source_note", "").strip() or None

    if not title:
        return redirect(url_for("schedule.index"))

    db.execute(
        """INSERT INTO schedules (title, date, type, goal_id, newsletter_id, source_note)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (title, schedule_date, schedule_type, goal_id, newsletter_id, source_note),
    )
    db.commit()
    return redirect(url_for("schedule.index"))


@bp.route("/<int:schedule_id>/toggle", methods=["POST"])
def toggle(schedule_id: int):
    db = get_db()
    row = db.execute("SELECT status FROM schedules WHERE id = ?", (schedule_id,)).fetchone()
    if row:
        new_status = "예정" if row["status"] == "완료" else "완료"
        db.execute("UPDATE schedules SET status = ? WHERE id = ?", (new_status, schedule_id))
        db.commit()
    return redirect(url_for("schedule.index"))


@bp.route("/<int:schedule_id>/delete", methods=["POST"])
def delete(schedule_id: int):
    db = get_db()
    db.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    db.commit()
    return redirect(url_for("schedule.index"))
