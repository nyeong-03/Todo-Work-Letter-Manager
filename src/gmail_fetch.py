"""Fetch recent emails from Gmail and turn them into newsletter rows.

Design choices that follow directly from the requirements:
  * Read-only: only ever calls messages.list / messages.get (GET requests).
  * Bounded: caller passes days + max_results, so we never sweep the whole
    inbox by accident.
  * "Looks like a newsletter": Gmail's own List-Unsubscribe header is a very
    reliable signal that a marketing/newsletter system (not a person) sent
    the email, so we use its presence as the filter.
  * We fetch the full body only for messages that already passed that
    filter, and classify_and_summarize() immediately -- the raw body is
    never returned to app.py/routes, only the derived summary/category/etc.
    (nothing here writes to the database; that's routes/gmail.py's job).
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import date, datetime
from email.utils import parseaddr, parsedate_to_datetime

from src.classifier import classify_and_summarize

HEADERS_FOR_FILTER = ["From", "Subject", "Date", "List-Unsubscribe"]


@dataclass
class FetchedNewsletter:
    title: str
    sender: str
    received_date: str  # YYYY-MM-DD
    category: str
    summary: str
    topics: str
    deadline: str | None
    source_link: str
    gmail_message_id: str


def _import_build():
    try:
        from googleapiclient.discovery import build
    except ImportError as error:
        from src.gmail_auth import GmailNotConfigured

        raise GmailNotConfigured(
            "Gmail 연동 패키지가 설치되어 있지 않습니다. "
            "'pip install -r requirements.txt'를 실행해 주세요."
        ) from error
    return build


def _header(headers: list[dict], name: str) -> str | None:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value")
    return None


def _decode_body(payload: dict) -> str:
    """Walk a Gmail message payload and return the best plain-text we can find."""

    def find_part(part: dict, mime_type: str) -> dict | None:
        if part.get("mimeType") == mime_type and part.get("body", {}).get("data"):
            return part
        for sub_part in part.get("parts", []) or []:
            found = find_part(sub_part, mime_type)
            if found:
                return found
        return None

    part = find_part(payload, "text/plain") or find_part(payload, "text/html")
    if not part:
        return ""
    raw = part["body"]["data"]
    text = base64.urlsafe_b64decode(raw.encode("utf-8")).decode("utf-8", errors="replace")
    if part.get("mimeType") == "text/html":
        # Extremely small HTML->text step. We only need enough plain text for
        # keyword matching / a short summary, not a pixel-perfect rendering.
        import re

        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_recent_newsletters(credentials, days: int, max_results: int = 30) -> list[FetchedNewsletter]:
    """Return newsletter-like messages from the last `days` days.

    Two-pass approach to stay read-only and bounded:
      1. List message IDs from the last `days` days (metadata call).
      2. For each, fetch headers only first; keep it only if List-Unsubscribe
         is present; only THEN fetch the full body for the kept ones.
    """
    build = _import_build()
    service = build("gmail", "v1", credentials=credentials)

    query = f"newer_than:{int(days)}d"
    list_response = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results)
        .execute()
    )
    message_ids = [m["id"] for m in list_response.get("messages", [])]

    results: list[FetchedNewsletter] = []
    for message_id in message_ids:
        metadata = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="metadata", metadataHeaders=HEADERS_FOR_FILTER)
            .execute()
        )
        headers = metadata.get("payload", {}).get("headers", [])
        if not _header(headers, "List-Unsubscribe"):
            continue  # doesn't look like a newsletter -- skip, don't fetch body

        subject = _header(headers, "Subject") or "(제목 없음)"
        _, sender_email = parseaddr(_header(headers, "From") or "")
        date_header = _header(headers, "Date")
        try:
            received = parsedate_to_datetime(date_header).date() if date_header else date.today()
        except (TypeError, ValueError):
            received = date.today()

        full_message = (
            service.users().messages().get(userId="me", id=message_id, format="full").execute()
        )
        body_text = _decode_body(full_message.get("payload", {}))

        classification = classify_and_summarize(subject, body_text, received_on=received)

        results.append(
            FetchedNewsletter(
                title=subject,
                sender=sender_email or "알 수 없음",
                received_date=received.isoformat(),
                category=classification.category,
                summary=classification.summary,
                topics=classification.topics,
                deadline=classification.deadline,
                source_link=f"https://mail.google.com/mail/u/0/#inbox/{message_id}",
                gmail_message_id=message_id,
            )
        )
        # body_text goes out of scope here and is never stored -- only the
        # FetchedNewsletter (summary/category/etc.) is returned to the caller.
    return results
