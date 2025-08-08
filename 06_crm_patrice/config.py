#!/usr/bin/env python3
"""
Centralized configuration for CRM Patrice utilities
"""

import os


def _parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


class Config:
    """Environment-backed configuration with sensible defaults."""

    # Document templates
    DEFAULT_PROMPTS_DOC_ID: str | None
    DEFAULT_TEMPLATES_DOC_ID: str | None
    DEFAULT_BLOG_DOC_ID: str | None
    DEFAULT_WEBINAR_DOC_ID: str | None
    DEFAULT_INSTAGRAM_DOC_ID: str | None
    DEFAULT_EMAIL_DOC_ID: str | None

    # Transcripts input
    TRANSCRIPTS_SPREADSHEET_ID: str | None
    TRANSCRIPTS_SHEET_NAME: str

    # Calendar output
    CALENDAR_SPREADSHEET_ID: str | None
    CALENDAR_TASKS_SHEET_NAME: str

    # Scheduling behavior
    WEEKS_TO_SCHEDULE: int
    MAX_CELLS_BELOW: int
    SPLIT_TASKS_IN_CALENDAR: bool
    SCHEDULE_START_WEEKDAY: str
    CONTENT_START_WEEKDAY: str
    CONTENT_DAYS_SPAN: int

    def __init__(self) -> None:
        # Templates
        self.DEFAULT_PROMPTS_DOC_ID = os.getenv("DEFAULT_PROMPTS_DOC_ID")
        self.DEFAULT_TEMPLATES_DOC_ID = os.getenv("DEFAULT_TEMPLATES_DOC_ID")
        self.DEFAULT_BLOG_DOC_ID = os.getenv("DEFAULT_BLOG_DOC_ID")
        self.DEFAULT_WEBINAR_DOC_ID = os.getenv("DEFAULT_WEBINAR_DOC_ID")
        self.DEFAULT_INSTAGRAM_DOC_ID = os.getenv("DEFAULT_INSTAGRAM_DOC_ID")
        self.DEFAULT_EMAIL_DOC_ID = os.getenv("DEFAULT_EMAIL_DOC_ID")

        # Transcripts
        self.TRANSCRIPTS_SPREADSHEET_ID = os.getenv("TRANSCRIPTS_SPREADSHEET_ID")
        self.TRANSCRIPTS_SHEET_NAME = os.getenv("TRANSCRIPTS_SHEET_NAME", "client_transcriptions")

        # Calendar
        self.CALENDAR_SPREADSHEET_ID = os.getenv("CALENDAR_SPREADSHEET_ID")
        self.CALENDAR_TASKS_SHEET_NAME = os.getenv("CALENDAR_TASKS_SHEET_NAME", "Tasks")

        # Scheduling
        self.WEEKS_TO_SCHEDULE = int(os.getenv("WEEKS_TO_SCHEDULE", "6"))
        self.MAX_CELLS_BELOW = int(os.getenv("MAX_CELLS_BELOW", "5"))
        self.SPLIT_TASKS_IN_CALENDAR = _parse_bool(os.getenv("SPLIT_TASKS_IN_CALENDAR", "true"), True)
        self.SCHEDULE_START_WEEKDAY = os.getenv("SCHEDULE_START_WEEKDAY", "MONDAY").strip().upper()
        # Content monitor defaults
        self.CONTENT_START_WEEKDAY = os.getenv("CONTENT_START_WEEKDAY", "MONDAY").strip().upper()
        self.CONTENT_DAYS_SPAN = int(os.getenv("CONTENT_DAYS_SPAN", "3"))

