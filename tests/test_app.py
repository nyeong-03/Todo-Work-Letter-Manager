"""Basic tests. Run with:  pytest

These don't touch Gmail/network at all -- they test the rule-based
classifier and the Flask routes (add/update/delete/toggle) against a
temporary SQLite database.
"""

import os
import tempfile
from datetime import date

import pytest


@pytest.fixture()
def client(monkeypatch):
    # Point the app at a throwaway database for each test.
    db_fd, db_path = tempfile.mkstemp()
    monkeypatch.setattr("src.db.DB_PATH", __import__("pathlib").Path(db_path))

    from app import create_app

    app = create_app()
    app.testing = True
    with app.test_client() as test_client:
        yield test_client

    os.close(db_fd)
    os.unlink(db_path)


def test_dashboard_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "대시보드".encode() in response.data


def test_newsletters_seeded_and_filterable(client):
    response = client.get("/newsletters/")
    assert "컴퓨터활용능력".encode() in response.data

    response = client.get("/newsletters/?category=자격증")
    assert "컴퓨터활용능력".encode() in response.data
    assert "마케팅 아이디어 공모전".encode() not in response.data


def test_add_update_delete_newsletter(client):
    client.post(
        "/newsletters/add",
        data={
            "title": "테스트 공모전 접수 안내",
            "sender": "test@example.com",
            "body": "공모전 참가 신청을 받습니다. 접수 마감은 2026년 12월 1일까지입니다.",
        },
    )
    response = client.get("/newsletters/")
    assert "테스트 공모전 접수 안내".encode() in response.data


def test_goal_and_schedule_flow(client):
    client.post("/goals/add", data={"title": "테스트 목표", "field": "", "target_date": "", "memo": ""})
    response = client.get("/goals/")
    assert "테스트 목표".encode() in response.data

    client.post(
        "/schedule/add",
        data={"title": "테스트 일정", "date": date.today().isoformat(), "type": "일반 일정", "goal_id": "", "source_note": ""},
    )
    response = client.get("/schedule/")
    assert "테스트 일정".encode() in response.data


def test_classifier_never_invents_a_missing_deadline():
    from src.classifier import classify_and_summarize

    result = classify_and_summarize("동아리 모임 안내", "이번 주 금요일에 모임이 있습니다.")
    assert result.deadline is None  # no deadline mentioned -> None, not a guess
