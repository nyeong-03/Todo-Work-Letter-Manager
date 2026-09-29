from datetime import date

from flask import Blueprint, redirect, render_template, request, url_for

from src.classifier import CATEGORIES, classify_and_summarize
from src.db import get_db
from src.gmail_auth import load_account

bp = Blueprint("newsletters", __name__, url_prefix="/newsletters")


@bp.route("/")
def index():
    db = get_db()
    category = request.args.get("category", "")
    search = request.args.get("q", "").strip()

    query = "SELECT * FROM newsletters WHERE 1=1"
    params: list = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (title LIKE ? OR summary LIKE ? OR topics LIKE ?)"
        like = f"%{search}%"
        params += [like, like, like]
    query += " ORDER BY id DESC"

    newsletters = db.execute(query, params).fetchall()
    goals = db.execute("SELECT id, title FROM goals ORDER BY title").fetchall()
    gmail_account = load_account(db)

    return render_template(
        "newsletters.html",
        newsletters=newsletters,
        categories=CATEGORIES,
        goals=goals,
        selected_category=category,
        search=search,
        gmail_account=gmail_account,
    )


@bp.route("/add", methods=["POST"])
def add():
    """Manual paste-in: title + body -> auto classify, user can edit after."""
    db = get_db()
    title = request.form.get("title", "").strip()
    sender = request.form.get("sender", "").strip() or None
    body = request.form.get("body", "").strip()

    if not title:
        return redirect(url_for("newsletters.index"))

    result = classify_and_summarize(title, body, received_on=date.today())
    db.execute(
        """INSERT INTO newsletters
           (title, sender, received_date, category, summary, body, topics, deadline, status, source)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, '새 소식', '직접 입력')""",
        (
            title, sender, date.today().isoformat(), result.category,
            result.summary, body, result.topics, result.deadline,
        ),
    )
    db.commit()
    return redirect(url_for("newsletters.index"))


@bp.route("/<int:newsletter_id>/update", methods=["POST"])
def update(newsletter_id: int):
    """Let the user correct the AI-suggested category/summary/status/goal."""
    db = get_db()
    category = request.form.get("category")
    summary = request.form.get("summary")
    status = request.form.get("status")
    goal_id = request.form.get("goal_id") or None

    db.execute(
        "UPDATE newsletters SET category = ?, summary = ?, status = ?, goal_id = ? WHERE id = ?",
        (category, summary, status, goal_id, newsletter_id),
    )
    db.commit()
    return redirect(url_for("newsletters.index"))


@bp.route("/<int:newsletter_id>/delete", methods=["POST"])
def delete(newsletter_id: int):
    db = get_db()
    db.execute("DELETE FROM newsletters WHERE id = ?", (newsletter_id,))
    db.commit()
    return redirect(url_for("newsletters.index"))


@bp.route("/<int:newsletter_id>/to-schedule", methods=["POST"])
def to_schedule(newsletter_id: int):
    """Copy this newsletter's deadline into a real schedule item.

    Per the spec, this never auto-confirms: it pre-fills the schedule form
    and the user still has to press 'save' on the schedule page. We do that
    by redirecting to the schedule page with the fields pre-filled via query
    params, rather than inserting directly.
    """
    db = get_db()
    newsletter = db.execute(
        "SELECT * FROM newsletters WHERE id = ?", (newsletter_id,)
    ).fetchone()
    if not newsletter:
        return redirect(url_for("newsletters.index"))

    return redirect(
        url_for(
            "schedule.index",
            prefill_title=newsletter["title"],
            prefill_date=newsletter["deadline"] if newsletter["deadline"] not in (None, "날짜 확인 필요") else "",
            prefill_type="접수 마감",
            prefill_goal_id=newsletter["goal_id"] or "",
            prefill_newsletter_id=newsletter["id"],
            prefill_source_note=f"뉴스레터: {newsletter['title']}",
        )
    )
