"""Sample data so the app has something to show on first run.

seed_if_empty() (called from app.py at startup) only inserts this data when
the tables are completely empty, so it never overwrites anything real.
"""

from datetime import date, timedelta

_TODAY = date.today()


def _in(days: int) -> str:
    return (_TODAY + timedelta(days=days)).isoformat()


SAMPLE_GOALS = [
    {
        "title": "컴퓨터활용능력 1급 취득",
        "field": "자격증",
        "target_date": _in(60),
        "memo": "필기 먼저 접수하고, 실기는 필기 합격 후 준비",
    },
    {
        "title": "마케팅 공모전 수상",
        "field": "공모전·대외활동",
        "target_date": _in(40),
        "memo": "팀 프로젝트, 3인 이상 팀 구성 필요",
    },
    {
        "title": "이번 학기 학점 관리 (4.0 이상)",
        "field": "학업·학교생활",
        "target_date": _in(90),
        "memo": "중간·기말고사 일정 놓치지 않기",
    },
]

# category is filled in by src.classifier.classify_and_summarize() for real
# Gmail imports; here we set it directly since this is fixed sample data.
SAMPLE_NEWSLETTERS = [
    {
        "title": "[한국산업인력공단] 2026년 하반기 컴퓨터활용능력 시험 일정 안내",
        "sender": "notice@q-net.or.kr",
        "received_date": _in(-1),
        "category": "자격증",
        "summary": "하반기 컴퓨터활용능력 1급/2급 필기·실기 시험 일정과 접수 기간을 안내하는 공지입니다.",
        "topics": "컴퓨터활용능력, 자격증 시험",
        "deadline": _in(20),
        "status": "새 소식",
        "source": "샘플",
        "source_link": None,
        "goal_title": "컴퓨터활용능력 1급 취득",
    },
    {
        "title": "2026 대학생 마케팅 아이디어 공모전 접수 시작",
        "sender": "contest@marketing-idea.kr",
        "received_date": _in(-2),
        "category": "공모전·대외활동",
        "summary": "대학생 대상 마케팅 아이디어 공모전으로, 3~5인 팀 참가가 가능하며 서류 접수 후 본선 발표 심사가 진행됩니다.",
        "topics": "공모전, 마케팅, 팀 프로젝트",
        "deadline": _in(35),
        "status": "새 소식",
        "source": "샘플",
        "source_link": None,
        "goal_title": "마케팅 공모전 수상",
    },
    {
        "title": "[교무처] 2026학년도 2학기 중간고사 시간표 안내",
        "sender": "academic@university.ac.kr",
        "received_date": _in(-3),
        "category": "학업·학교생활",
        "summary": "2학기 중간고사 시간표가 공지되었습니다. 정확한 고사장은 추후 별도 안내 예정입니다.",
        "topics": "중간고사, 시간표",
        "deadline": "날짜 확인 필요",
        "status": "확인함",
        "source": "샘플",
        "source_link": None,
        "goal_title": "이번 학기 학점 관리 (4.0 이상)",
    },
    {
        "title": "삼일PwC 2026 겨울 인턴십 채용 설명회 안내",
        "sender": "careers@pwc.com",
        "received_date": _in(-5),
        "category": "취업·진로",
        "summary": "회계법인 겨울 인턴십 프로그램 채용 설명회 일정과 지원 방법을 안내하는 메일입니다.",
        "topics": "인턴십, 채용설명회, 회계법인",
        "deadline": _in(15),
        "status": "새 소식",
        "source": "샘플",
        "source_link": None,
        "goal_title": None,
    },
    {
        "title": "동아리 정기 모임 및 MT 일정 공지",
        "sender": "club@university.ac.kr",
        "received_date": _in(-1),
        "category": "기타",
        "summary": "동아리 정기 모임과 다음 달 MT 일정을 공지하는 메일입니다.",
        "topics": "동아리, MT",
        "deadline": None,
        "status": "보관함",
        "source": "샘플",
        "source_link": None,
        "goal_title": None,
    },
]

SAMPLE_SCHEDULES = [
    {
        "title": "컴퓨터활용능력 필기 접수",
        "date": _in(20),
        "type": "접수 마감",
        "status": "예정",
        "goal_title": "컴퓨터활용능력 1급 취득",
        "newsletter_title": "[한국산업인력공단] 2026년 하반기 컴퓨터활용능력 시험 일정 안내",
        "source_note": "Q-net 공지 메일",
    },
    {
        "title": "마케팅 공모전 팀 구성 완료",
        "date": _in(10),
        "type": "준비 할 일",
        "status": "예정",
        "goal_title": "마케팅 공모전 수상",
        "newsletter_title": None,
        "source_note": "스스로 정한 목표",
    },
    {
        "title": "마케팅 공모전 서류 접수",
        "date": _in(35),
        "type": "접수 마감",
        "status": "예정",
        "goal_title": "마케팅 공모전 수상",
        "newsletter_title": "2026 대학생 마케팅 아이디어 공모전 접수 시작",
        "source_note": "공모전 안내 메일",
    },
    {
        "title": "중간고사 기간",
        "date": _in(25),
        "type": "시험일",
        "status": "예정",
        "goal_title": "이번 학기 학점 관리 (4.0 이상)",
        "newsletter_title": "[교무처] 2026학년도 2학기 중간고사 시간표 안내",
        "source_note": "교무처 공지",
    },
    {
        "title": "삼일PwC 인턴십 설명회 참석",
        "date": _in(15),
        "type": "행사일",
        "status": "예정",
        "goal_title": None,
        "newsletter_title": "삼일PwC 2026 겨울 인턴십 채용 설명회 안내",
        "source_note": "채용 메일",
    },
    {
        "title": "지난 학기 장학금 신청",
        "date": _in(-10),
        "type": "접수 마감",
        "status": "완료",
        "goal_title": None,
        "newsletter_title": None,
        "source_note": "직접 추가",
    },
]


def seed_if_empty(db) -> None:
    """Insert the sample dataset, but only if the app has no data at all."""
    existing = db.execute("SELECT COUNT(*) FROM newsletters").fetchone()[0]
    if existing > 0:
        return  # already has real (or previously seeded) data -- never overwrite

    goal_ids: dict[str, int] = {}
    for goal in SAMPLE_GOALS:
        cursor = db.execute(
            "INSERT INTO goals (title, field, target_date, memo) VALUES (?, ?, ?, ?)",
            (goal["title"], goal["field"], goal["target_date"], goal["memo"]),
        )
        goal_ids[goal["title"]] = cursor.lastrowid

    newsletter_ids: dict[str, int] = {}
    for item in SAMPLE_NEWSLETTERS:
        cursor = db.execute(
            """INSERT INTO newsletters
               (title, sender, received_date, category, summary, topics,
                deadline, status, source, source_link, goal_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                item["title"], item["sender"], item["received_date"], item["category"],
                item["summary"], item["topics"], item["deadline"], item["status"],
                item["source"], item["source_link"], goal_ids.get(item["goal_title"]),
            ),
        )
        newsletter_ids[item["title"]] = cursor.lastrowid

    for item in SAMPLE_SCHEDULES:
        db.execute(
            """INSERT INTO schedules
               (title, date, type, status, goal_id, newsletter_id, source_note)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                item["title"], item["date"], item["type"], item["status"],
                goal_ids.get(item["goal_title"]),
                newsletter_ids.get(item["newsletter_title"]),
                item["source_note"],
            ),
        )
    db.commit()
