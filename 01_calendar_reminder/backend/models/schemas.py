from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Any, Dict
from datetime import datetime


# Authentication Models
class AuthStatus(BaseModel):
    authenticated: bool


# Calendar Event Models
class CalendarEvent(BaseModel):
    id: Optional[str] = None
    summary: str
    description: Optional[str] = None
    start: Dict[str, Any]
    end: Dict[str, Any]
    location: Optional[str] = None
    attendees: Optional[List[Dict[str, str]]] = None
    htmlLink: Optional[str] = None


class CreateEventRequest(BaseModel):
    title: str
    start: str
    end: str
    description: Optional[str] = ""
    location: Optional[str] = ""
    attendees: Optional[List[str]] = []


# Text Parsing Models
class ParsedEvent(BaseModel):
    title: str = Field(..., description="Event title")
    start: str = Field(..., description="Start datetime in ISO 8601 format")
    end: str = Field(..., description="End datetime in ISO 8601 format")
    timezone: str = Field(..., description="IANA timezone")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")
    attendees: Optional[List[str]] = Field(None, description="List of attendee emails")


class EventParsingOutput(BaseModel):
    events: List[ParsedEvent] = Field(..., description="List of parsed events")


class ParseTextRequest(BaseModel):
    text: str
    openai_api_key: str


class ParseTextResponse(BaseModel):
    message: str
    events_created: int
    events_failed: int
    created_events: List[Dict[str, Any]]
    failed_events: List[Dict[str, Any]]
    parsed_text: str


# Chat Models
class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    openai_api_key: str


class ChatResponse(BaseModel):
    response: str


# Telegram Models
class TelegramRequest(BaseModel):
    bot_token: str
    chat_id: str


class TelegramTestRequest(TelegramRequest):
    pass


class DailyScheduleResponse(BaseModel):
    message: str
    events_count: int
    date: Optional[str] = None


# Scheduler Models
class ScheduleReminderRequest(BaseModel):
    bot_token: str
    chat_id: str
    hour: int = 9
    minute: int = 0
    enabled: bool = True
    user_id: str = "default_user"


class ReminderStatusResponse(BaseModel):
    scheduled: bool
    enabled: bool
    hour: Optional[int] = None
    minute: Optional[int] = None
    next_run: Optional[str] = None
    user_id: str


class TestScheduleRequest(BaseModel):
    bot_token: str
    chat_id: str


class TestScheduleResponse(BaseModel):
    message: str
    scheduled_time: str 