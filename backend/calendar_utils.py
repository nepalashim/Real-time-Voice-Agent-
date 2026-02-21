"""
Google Calendar authentication and event insertion utilities.

Supports two auth modes:
  1. Service Account – set GOOGLE_SERVICE_ACCOUNT_FILE in .env
     (recommended for server-to-server use).
  2. OAuth2 Desktop flow – set GOOGLE_CREDENTIALS_FILE in .env
     (token.json is cached after first consent).
"""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]

# ── Paths from environment ───────────────────────────────────────────
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")  # path to JSON key
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")          # OAuth2 client secret
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")


def _get_credentials() -> Credentials:
    """Return valid Google credentials, refreshing or prompting as needed."""

    # ── Option 1: Service Account ────────────────────────────────────
    if SERVICE_ACCOUNT_FILE and os.path.exists(SERVICE_ACCOUNT_FILE):
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        return creds

    # ── Option 2: OAuth2 (Desktop / Installed App) ───────────────────
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE or not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    "No valid Google credentials found. "
                    "Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_CREDENTIALS_FILE in .env"
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the token for next run
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return creds


def get_calendar_service():
    """Build and return an authorized Google Calendar API service."""
    creds = _get_credentials()
    return build("calendar", "v3", credentials=creds)


def create_event(
    name: str,
    start_time: str,
    end_time: str | None = None,
    title: str | None = None,
) -> dict:
    """
    Insert a calendar event and return the created event resource.

    Parameters
    ----------
    name : str
        Attendee / requester name (added to description).
    start_time : str
        ISO 8601 datetime string for event start.
    end_time : str | None
        ISO 8601 datetime string for event end.
        Defaults to 30 minutes after start_time.
    title : str | None
        Event summary / title. Defaults to "Meeting with <name>".
    """
    service = get_calendar_service()

    # Parse & default end_time
    dt_start = datetime.fromisoformat(start_time)
    if end_time:
        dt_end = datetime.fromisoformat(end_time)
    else:
        dt_end = dt_start + timedelta(minutes=30)

    event_title = title if title else f"Meeting with {name}"

    event_body = {
        "summary": event_title,
        "description": f"Scheduled by Voice AI Agent for {name}.",
        "start": {
            "dateTime": dt_start.isoformat(),
            "timeZone": os.getenv("TIMEZONE", "UTC"),
        },
        "end": {
            "dateTime": dt_end.isoformat(),
            "timeZone": os.getenv("TIMEZONE", "UTC"),
        },
    }

    created = (
        service.events()
        .insert(calendarId=CALENDAR_ID, body=event_body)
        .execute()
    )
    return created
