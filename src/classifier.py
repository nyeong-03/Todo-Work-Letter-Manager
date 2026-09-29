"""Turn a raw (subject, body) pair into (category, summary, topics, deadline).

This module has no external dependencies and no API key requirement, so the
app works fully offline / without any AI key. It is deliberately isolated
from the rest of the app so it can be swapped for a real LLM call later --
see the "실제 AI로 교체하기" section in README.md.

classify_and_summarize() is the one function the rest of the app calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta

CATEGORIES = ["자격증", "공모전·대외활동", "학업·학교생활", "취업·진로", "기타"]

# Very small keyword lists. Not exhaustive on purpose -- good enough for a
# demo/MVP, and easy for a beginner to read and extend.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "자격증": ["자격증", "필기", "실기", "합격자", "시험 일정", "큐넷", "q-net", "토익", "토픽", "산업인력공단"],
    "공모전·대외활동": ["공모전", "대외활동", "서포터즈", "해커톤", "경진대회", "아이디어 공모"],
    "학업·학교생활": ["수강신청", "중간고사", "기말고사", "학사", "교무처", "휴학", "복학", "성적", "장학금", "학점"],
    "취업·진로": ["채용", "인턴", "인턴십", "공채", "직무", "이력서", "자기소개서", "설명회", "면접"],
}

# Sentences containing these words are more likely to hold the actual deadline
# (as opposed to some other date mentioned in passing).
_DEADLINE_HINTS = ["마감", "까지", "접수기간", "접수 기간", "신청기간", "신청 기간"]

_DATE_PATTERNS = [
    # 2026년 10월 9일 / 2026. 10. 9 / 2026-10-09
    re.compile(r"(\d{4})\s*[년.\-]\s*(\d{1,2})\s*[월.\-]\s*(\d{1,2})\s*일?"),
    # 10월 9일 (연도 없이 - 올해 또는 내년으로 추정하지 않고, 연도 없는 날짜는 신뢰도가 낮아 무시)
]


@dataclass
class ClassificationResult:
    category: str
    summary: str
    topics: str  # comma-separated
    deadline: str | None  # ISO date string, "날짜 확인 필요", or None


def _guess_category(text: str) -> str:
    scores = {category: 0 for category in CATEGORY_KEYWORDS}
    lowered = text.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in lowered:
                scores[category] += 1
    best_category = max(scores, key=scores.get)
    return best_category if scores[best_category] > 0 else "기타"


def _first_sentences(text: str, max_chars: int = 150) -> str:
    """A dumb but honest 'summary': the first sentence or two, trimmed.

    We never invent content the source didn't say -- this just shortens it.
    """
    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return "본문 내용이 없어 요약할 수 없습니다."
    if len(cleaned) <= max_chars:
        return cleaned
    # Try to cut at a sentence boundary near the limit
    snippet = cleaned[:max_chars]
    last_boundary = max(snippet.rfind(". "), snippet.rfind("다. "), snippet.rfind("요. "))
    if last_boundary > 40:
        snippet = snippet[: last_boundary + 1]
    return snippet.strip() + "…"


def _extract_topics(text: str, category: str, max_topics: int = 4) -> str:
    found = []
    for keyword in CATEGORY_KEYWORDS.get(category, []):
        if keyword.lower() in text.lower() and keyword not in found:
            found.append(keyword)
        if len(found) >= max_topics:
            break
    return ", ".join(found) if found else category


def extract_deadline(text: str, received_on: date | None = None) -> str | None:
    """Find a deadline-looking date in the text.

    Returns an ISO date string when confident, "날짜 확인 필요" when the text
    clearly talks about a deadline but we can't parse a reliable date, and
    None when there's no sign of a deadline at all.
    """
    lines_with_hint = [
        line for line in re.split(r"[\n.]", text) if any(hint in line for hint in _DEADLINE_HINTS)
    ]
    search_space = "\n".join(lines_with_hint) if lines_with_hint else ""

    for pattern in _DATE_PATTERNS:
        match = pattern.search(search_space)
        if match:
            year, month, day = (int(part) for part in match.groups())
            try:
                parsed = date(year, month, day)
            except ValueError:
                continue
            # Sanity check: reject dates absurdly far in the past/future --
            # more likely a mis-parse than an actual deadline.
            if received_on and abs((parsed - received_on).days) > 730:
                continue
            return parsed.isoformat()

    if lines_with_hint:
        return "날짜 확인 필요"
    return None


def classify_and_summarize(subject: str, body: str, received_on: date | None = None) -> ClassificationResult:
    """Main entry point used by both manual paste-in and Gmail import."""
    combined = f"{subject}\n{body}"
    category = _guess_category(combined)
    summary = _first_sentences(body or subject)
    topics = _extract_topics(combined, category)
    deadline = extract_deadline(combined, received_on)
    return ClassificationResult(category=category, summary=summary, topics=topics, deadline=deadline)
