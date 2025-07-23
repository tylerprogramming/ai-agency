from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class DeleteEventInput(BaseModel):
    event_id: str = Field(..., description="The unique ID of the event to delete")

class DeleteEventTool(BaseTool):
    name: str = "Delete Google Calendar Event"
    description: str = (
        "Deletes an event from the user's Google Calendar using the event ID. "
        "Use this when the user wants to remove an existing event."
    )
    args_schema: Type[BaseModel] = DeleteEventInput

    def _run(self, event_id: str) -> str:
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
            
            # First, try to get the event to verify it exists and get its title
            try:
                event = service.events().get(calendarId='primary', eventId=event_id).execute()
                event_title = event.get('summary', 'Untitled Event')
            except Exception:
                return f"Error: Event with ID '{event_id}' not found or you don't have permission to access it."
            
            # Delete the event
            service.events().delete(calendarId='primary', eventId=event_id).execute()
            return f"Successfully deleted event: '{event_title}' (ID: {event_id})"
            
        except Exception as e:
            return f"Error deleting event: {str(e)}"