"""Load configuration from environment variables (see .env.example)."""

import os

from dotenv import load_dotenv

load_dotenv()  # reads a local .env file if present; never overrides real env vars

FLASK_SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.environ.get("GOOGLE_REDIRECT_URI", "http://localhost:5000/gmail/callback")
