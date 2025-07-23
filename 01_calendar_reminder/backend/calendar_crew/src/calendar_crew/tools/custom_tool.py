from crewai.tools import BaseTool
from typing import Type, List, Optional
from pydantic import BaseModel, Field, EmailStr
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class AddEventInput(BaseModel):
    title: str = Field(..., description="Event title")
    start: str = Field(..., description="Start datetime in ISO 8601 format, e.g. '2024-07-01T10:00:00'")
    end: str = Field(..., description="End datetime in ISO 8601 format, e.g. '2024-07-01T11:00:00'")
    timezone: str = Field(..., description="IANA time zone, e.g. 'America/Los_Angeles' or 'UTC'")
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, description="Event location")
    attendees: Optional[List[EmailStr]] = Field(None, description="List of attendee emails")

class AddEventTool(BaseTool):
    name: str = "Add Google Calendar Event"
    description: str = (
        "Creates a new event in the user's Google Calendar. Use this when the user wants to add a new event."
    )
    args_schema: Type[BaseModel] = AddEventInput

    def _run(self, title: str, start: str, end: str, timezone: str, description: Optional[str] = None, location: Optional[str] = None, attendees: Optional[List[str]] = None) -> str:
        # Authenticate and build the Google Calendar service
        token_path = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                '../../../../../calendar_credentials/calendar_token.json'
            )
        )
        scopes = ['https://www.googleapis.com/auth/calendar.events']
        creds = Credentials.from_authorized_user_file(token_path, scopes)
        service = build('calendar', 'v3', credentials=creds)
        event = {
            'summary': title,
            'start': {'dateTime': start, 'timeZone': timezone},
            'end': {'dateTime': end, 'timeZone': timezone},
        }
        if description:
            event['description'] = description
        if location:
            event['location'] = location
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return f"Event created: {created_event.get('htmlLink', 'No link available')}"
