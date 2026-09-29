"""Entry point. Run with:  python app.py

This wires together the database, sample-data seeding, and every screen's
blueprint (dashboard / newsletters / goals / schedule / gmail).
"""

import os

from flask import Flask

import config
from src.db import close_db, get_db, init_db
from src.routes import dashboard, gmail, goals, newsletters, schedule
from src.sample_data import seed_if_empty


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = config.FLASK_SECRET_KEY

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(newsletters.bp)
    app.register_blueprint(goals.bp)
    app.register_blueprint(schedule.bp)
    app.register_blueprint(gmail.bp)

    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()
        seed_if_empty(get_db())

    @app.template_filter("status_class")
    def status_class(value: str) -> str:
        """'새 소식' -> 'status-new', so it's always a single safe CSS class."""
        mapping = {"새 소식": "status-new", "확인함": "status-checked", "보관함": "status-archived"}
        return mapping.get(value, "status-other")

    @app.template_filter("d")
    def format_date(value):
        """Template helper: turn '2026-10-09' into '10월 9일' for nicer display."""
        if not value or value in ("날짜 확인 필요",):
            return value or ""
        try:
            from datetime import date

            year, month, day = (int(part) for part in value.split("-"))
            return f"{month}월 {day}일"
        except (ValueError, AttributeError):
            return value

    return app


app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="127.0.0.1", port=5000, debug=debug)
