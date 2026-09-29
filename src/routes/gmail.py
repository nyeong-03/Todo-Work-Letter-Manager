from flask import Blueprint, flash, redirect, request, session, url_for

from src.classifier import CATEGORIES
from src.db import get_db
from src.gmail_auth import (
    GmailNotConfigured,
    build_auth_url,
    disconnect as gmail_disconnect,
    exchange_code_for_credentials,
    get_user_email,
    load_credentials,
    save_credentials,
    update_last_synced,
)
from src.gmail_fetch import fetch_recent_newsletters

bp = Blueprint("gmail", __name__, url_prefix="/gmail")


@bp.route("/connect")
def connect():
    """Step 1: send the user to Google's consent screen."""
    try:
        auth_url, state = build_auth_url()
    except GmailNotConfigured as error:
        flash(str(error), "error")
        return redirect(url_for("newsletters.index"))

    session["gmail_oauth_state"] = state
    return redirect(auth_url)


@bp.route("/callback")
def callback():
    """Step 2: Google redirects back here with ?code=... after the user approves."""
    error = request.args.get("error")
    if error:
        flash(f"Google 인증이 취소되었거나 실패했습니다: {error}", "error")
        return redirect(url_for("newsletters.index"))

    code = request.args.get("code")
    if not code:
        flash("Google로부터 인증 코드를 받지 못했습니다.", "error")
        return redirect(url_for("newsletters.index"))

    try:
        credentials = exchange_code_for_credentials(code)
        email = get_user_email(credentials)
        db = get_db()
        save_credentials(db, email, credentials)
    except GmailNotConfigured as config_error:
        flash(str(config_error), "error")
        return redirect(url_for("newsletters.index"))
    except Exception as unexpected_error:  # network/API errors from Google
        flash(f"Gmail 연결 중 오류가 발생했습니다: {unexpected_error}", "error")
        return redirect(url_for("newsletters.index"))

    flash(f"{email} 계정이 연결되었습니다.", "success")
    return redirect(url_for("newsletters.index"))


@bp.route("/sync", methods=["POST"])
def sync():
    """Fetch newsletter-like mail from the last N days and save summaries only."""
    db = get_db()
    try:
        credentials = load_credentials(db)
    except GmailNotConfigured as error:
        flash(str(error), "error")
        return redirect(url_for("newsletters.index"))

    if not credentials:
        flash("먼저 Gmail 계정을 연결해 주세요.", "error")
        return redirect(url_for("newsletters.index"))

    days = int(request.form.get("days", 7))
    days = max(1, min(days, 90))  # bounded: never more than 90 days at once

    try:
        fetched = fetch_recent_newsletters(credentials, days=days, max_results=30)
    except GmailNotConfigured as error:
        flash(str(error), "error")
        return redirect(url_for("newsletters.index"))
    except Exception as unexpected_error:
        flash(f"메일을 가져오는 중 오류가 발생했습니다: {unexpected_error}", "error")
        return redirect(url_for("newsletters.index"))

    existing_ids = {
        row["source_link"]
        for row in db.execute(
            "SELECT source_link FROM newsletters WHERE source = 'Gmail'"
        ).fetchall()
    }

    added = 0
    for item in fetched:
        if item.source_link in existing_ids:
            continue  # already imported this exact email before
        category = item.category if item.category in CATEGORIES else "기타"
        db.execute(
            """INSERT INTO newsletters
               (title, sender, received_date, category, summary, topics,
                deadline, status, source, source_link)
               VALUES (?, ?, ?, ?, ?, ?, ?, '새 소식', 'Gmail', ?)""",
            (
                item.title, item.sender, item.received_date, category,
                item.summary, item.topics, item.deadline, item.source_link,
            ),
        )
        added += 1
    update_last_synced(db)
    db.commit()

    flash(f"최근 {days}일간 메일에서 뉴스레터 {added}건을 새로 가져왔습니다.", "success")
    return redirect(url_for("newsletters.index"))


@bp.route("/disconnect", methods=["POST"])
def disconnect():
    """Revoke the local connection. Previously-imported newsletters stay,
    unless the user also asked to delete them (checkbox in the form)."""
    db = get_db()
    gmail_disconnect(db)

    if request.form.get("delete_imported") == "on":
        db.execute("DELETE FROM newsletters WHERE source = 'Gmail'")
        db.commit()
        flash("Gmail 연결을 해제하고, 가져온 뉴스레터도 모두 삭제했습니다.", "success")
    else:
        flash("Gmail 연결을 해제했습니다. 이미 가져온 뉴스레터는 남아 있습니다.", "success")

    return redirect(url_for("newsletters.index"))
