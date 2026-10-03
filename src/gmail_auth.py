"""Gmail OAuth 2.0 (read-only) helpers.

Google libraries (google-auth, google-auth-oauthlib, google-api-python-client)
are imported lazily, inside functions, not at module load time. That way the
rest of the app still runs even before `pip install -r requirements.txt` has
pulled these in, and gives a clear error message pointing at requirements.txt
instead of crashing the whole app at startup.

Scope is read-only, on purpose: https://www.googleapis.com/auth/gmail.readonly
This app never requests send/modify/delete permission.
"""

from __future__ import annotations

import os
from typing import Any

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailNotConfigured(Exception):
    """Raised when required env vars or packages are missing."""


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise GmailNotConfigured(
            f"{name} 환경변수가 설정되어 있지 않습니다. .env 파일을 확인해 주세요."
        )
    return value


def _client_config() -> dict[str, Any]:
    return {
        "web": {
            "client_id": _require_env("GOOGLE_CLIENT_ID"),
            "client_secret": _require_env("GOOGLE_CLIENT_SECRET"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [_require_env("GOOGLE_REDIRECT_URI")],
        }
    }


def _import_flow():
    try:
        from google_auth_oauthlib.flow import Flow
    except ImportError as error:  # pragma: no cover - exercised only without deps installed
        raise GmailNotConfigured(
            "Gmail 연동 패키지가 설치되어 있지 않습니다. "
            "'pip install -r requirements.txt'를 실행해 주세요."
        ) from error
    return Flow


def _import_build():
    try:
        from googleapiclient.discovery import build
    except ImportError as error:  # pragma: no cover - exercised only without deps installed
        raise GmailNotConfigured(
            "Gmail 연동 패키지가 설치되어 있지 않습니다. "
            "'pip install -r requirements.txt'를 실행해 주세요."
        ) from error
    return build


def build_auth_url() -> tuple[str, str, str]:
    """Return (consent_screen_url, state, code_verifier).

    google-auth-oauthlib enables PKCE by default: it generates a random
    code_verifier and sends a hash of it (code_challenge) to Google. Google
    later checks the *original* code_verifier at the token-exchange step, so
    we must hand it back to the caller to store (in the Flask session) and
    reuse in exchange_code_for_credentials() -- a fresh Flow object built
    later has no memory of it otherwise, which is what caused the
    "Missing code verifier" error.
    """
    Flow = _import_flow()
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES)
    flow.redirect_uri = _require_env("GOOGLE_REDIRECT_URI")
    auth_url, state = flow.authorization_url(
        access_type="offline",       # needed to receive a refresh_token
        include_granted_scopes="true",
        prompt="consent",            # forces a refresh_token even on repeat connects
    )
    return auth_url, state, flow.code_verifier


def exchange_code_for_credentials(code: str, code_verifier: str | None = None):
    """Exchange the ?code=... callback param for real OAuth credentials.

    code_verifier must be the same value build_auth_url() returned for this
    login attempt (see the PKCE note above) -- pass it through from the
    session, or token exchange will fail with 'Missing code verifier'.
    """
    Flow = _import_flow()
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES)
    flow.redirect_uri = _require_env("GOOGLE_REDIRECT_URI")
    if code_verifier:
        flow.code_verifier = code_verifier
    flow.fetch_token(code=code)
    return flow.credentials


def credentials_to_row(credentials) -> dict[str, Any]:
    return {
        "refresh_token": credentials.refresh_token,
        "access_token": credentials.token,
        "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }


def save_credentials(db, email: str, credentials) -> None:
    row = credentials_to_row(credentials)
    db.execute(
        """INSERT INTO gmail_account (id, email, refresh_token, access_token, token_expiry)
           VALUES (1, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
             email = excluded.email,
             refresh_token = excluded.refresh_token,
             access_token = excluded.access_token,
             token_expiry = excluded.token_expiry""",
        (email, row["refresh_token"], row["access_token"], row["token_expiry"]),
    )
    db.commit()


def load_account(db) -> dict[str, Any] | None:
    row = db.execute("SELECT * FROM gmail_account WHERE id = 1").fetchone()
    return dict(row) if row else None


def load_credentials(db):
    """Rebuild a Credentials object from the stored refresh token, if any."""
    row = load_account(db)
    if not row:
        return None
    try:
        from google.oauth2.credentials import Credentials
    except ImportError as error:
        raise GmailNotConfigured(
            "Gmail 연동 패키지가 설치되어 있지 않습니다. "
            "'pip install -r requirements.txt'를 실행해 주세요."
        ) from error
    return Credentials(
        token=row["access_token"],
        refresh_token=row["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=_require_env("GOOGLE_CLIENT_ID"),
        client_secret=_require_env("GOOGLE_CLIENT_SECRET"),
        scopes=SCOPES,
    )


def get_user_email(credentials) -> str:
    """Ask Gmail itself who this token belongs to.

    We deliberately do NOT call Google's separate /oauth2/v2/userinfo
    endpoint here: that endpoint needs its own 'email'/'profile' scope,
    which we don't request (we only ask for gmail.readonly, per the
    "read-only only" requirement). Gmail API's own users().getProfile()
    call returns the account's email address and is already covered by
    the gmail.readonly scope we do have.
    """
    build = _import_build()
    service = build("gmail", "v1", credentials=credentials)
    profile = service.users().getProfile(userId="me").execute()
    return profile.get("emailAddress", "알 수 없음")


def update_last_synced(db) -> None:
    db.execute("UPDATE gmail_account SET last_synced_at = datetime('now') WHERE id = 1")
    db.commit()


def disconnect(db) -> None:
    """Remove the stored token. Does NOT touch already-imported newsletters --
    those stay as normal data the user can delete separately if they want."""
    db.execute("DELETE FROM gmail_account WHERE id = 1")
    db.commit()
