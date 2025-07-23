from crewai.tools import BaseTool
from typing import Type, List, Optional
from pydantic import BaseModel, Field, EmailStr
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class UpdateEventInput(BaseModel):
    event_id: str = Field(..., description="The unique ID of the event to update")
    title: Optional[str] = Field(None, description="New event title (leave None to keep existing)")
    start: Optional[str] = Field(None, description="New start datetime in ISO 8601 format, e.g. '2024-07-01T10:00:00'")
    end: Optional[str] = Field(None, description="New end datetime in ISO 8601 format, e.g. '2024-07-01T11:00:00'")
    timezone: Optional[str] = Field(None, description="New IANA time zone, e.g. 'America/Los_Angeles' or 'UTC'")
    description: Optional[str] = Field(None, description="New event description")
    location: Optional[str] = Field(None, description="New event location")
    attendees: Optional[List[EmailStr]] = Field(None, description="New list of attendee emails")

class UpdateEventTool(BaseTool):
    name: str = "Update Google Calendar Event"
    description: str = (
        "Updates an existing event in the user's Google Calendar. "
        "Only the fields you specify will be updated, others remain unchanged. "
        "Use this when the user wants to modify an existing event."
    )
    args_schema: Type[BaseModel] = UpdateEventInput

    def _run(self, event_id: str, title: Optional[str] = None, start: Optional[str] = None, 
             end: Optional[str] = None, timezone: Optional[str] = None, description: Optional[str] = None, 
             location: Optional[str] = None, attendees: Optional[List[str]] = None) -> str:
        try:
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
            
            # First, get the existing event
            try:
                existing_event = service.events().get(calendarId='primary', eventId=event_id).execute()
            except Exception:
                return f"Error: Event with ID '{event_id}' not found or you don't have permission to access it."
            
            # Update only the specified fields
            updated_fields = []
            
            if title is not None:
                existing_event['summary'] = title
                updated_fields.append('title')
            
            if start is not None or end is not None or timezone is not None:
                # Handle time updates
                if start is not None:
                    if timezone is not None:
                        existing_event['start'] = {'dateTime': start, 'timeZone': timezone}
                    else:
                        existing_event['start']['dateTime'] = start
                    updated_fields.append('start time')
                
                if end is not None:
                    if timezone is not None:
                        existing_event['end'] = {'dateTime': end, 'timeZone': timezone}
                    else:
                        existing_event['end']['dateTime'] = end
                    updated_fields.append('end time')
                
                if timezone is not None and start is None and end is None:
                    # Update timezone for existing times
                    existing_event['start']['timeZone'] = timezone
                    existing_event['end']['timeZone'] = timezone
                    updated_fields.append('timezone')
            
            if description is not None:
                existing_event['description'] = description
                updated_fields.append('description')
            
            if location is not None:
                existing_event['location'] = location
                updated_fields.append('location')
            
            if attendees is not None:
                existing_event['attendees'] = [{'email': email} for email in attendees]
                updated_fields.append('attendees')
            
            # Update the event
            updated_event = service.events().update(
                calendarId='primary', 
                eventId=event_id, 
                body=existing_event
            ).execute()
            
            event_title = updated_event.get('summary', 'Untitled Event')
            updated_fields_str = ', '.join(updated_fields) if updated_fields else 'no fields'
            
            return f"Successfully updated event: '{event_title}' (ID: {event_id}). Updated fields: {updated_fields_str}. Link: {updated_event.get('htmlLink', 'No link available')}"
            
        except Exception as e:
            return f"Error updating event: {str(e)}"