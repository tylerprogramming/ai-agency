from crewai.tools import BaseTool
from typing import Type, Optional
from pydantic import BaseModel, Field
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json

class SelectEventsInput(BaseModel):
    start_date: Optional[str] = Field(None, description="Start date for search in ISO 8601 format, e.g. '2024-07-01T00:00:00'. If not provided, searches from today.")
    end_date: Optional[str] = Field(None, description="End date for search in ISO 8601 format, e.g. '2024-07-31T23:59:59'. If not provided, searches until one month from start_date.")
    query: Optional[str] = Field(None, description="Text to search for in event titles and descriptions")
    max_results: Optional[int] = Field(50, description="Maximum number of events to return (default: 50, max: 2500)")

class SelectEventsTool(BaseTool):
    name: str = "Select Google Calendar Events"
    description: str = (
        "Searches and retrieves events from the user's Google Calendar. "
        "Can filter by date range and search text. Returns detailed event information including IDs for further operations. "
        "Use this to find, list, or search for existing events."
    )
    args_schema: Type[BaseModel] = SelectEventsInput

    def _run(self, start_date: Optional[str] = None, end_date: Optional[str] = None, 
             query: Optional[str] = None, max_results: Optional[int] = 50) -> str:
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
            
            # Set default date range if not provided
            if start_date is None:
                start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                start_date = start_dt.isoformat() + 'Z'
            else:
                start_date = start_date + 'Z' if not start_date.endswith('Z') else start_date
            
            if end_date is None:
                # Default to one month from start date
                start_dt = datetime.fromisoformat(start_date.replace('Z', ''))
                end_dt = start_dt + timedelta(days=31)
                end_date = end_dt.isoformat() + 'Z'
            else:
                end_date = end_date + 'Z' if not end_date.endswith('Z') else end_date
            
            # Ensure max_results is within bounds
            max_results = min(max_results or 50, 2500)
            
            # Build the search parameters
            search_params = {
                'calendarId': 'primary',
                'timeMin': start_date,
                'timeMax': end_date,
                'maxResults': max_results,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            
            # Add text query if provided
            if query:
                search_params['q'] = query
            
            # Execute the search
            events_result = service.events().list(**search_params).execute()
            events = events_result.get('items', [])
            
            if not events:
                return f"No events found for the specified criteria. Search period: {start_date} to {end_date}" + (f", Query: '{query}'" if query else "")
            
            # Format the results
            formatted_events = []
            for event in events:
                event_info = {
                    'id': event.get('id'),
                    'title': event.get('summary', 'No Title'),
                    'description': event.get('description', ''),
                    'location': event.get('location', ''),
                    'status': event.get('status', ''),
                    'html_link': event.get('htmlLink', ''),
                    'created': event.get('created', ''),
                    'updated': event.get('updated', '')
                }
                
                # Handle start and end times
                start_info = event.get('start', {})
                end_info = event.get('end', {})
                
                if 'dateTime' in start_info:
                    event_info['start_datetime'] = start_info['dateTime']
                    event_info['start_timezone'] = start_info.get('timeZone', 'UTC')
                    event_info['all_day'] = False
                elif 'date' in start_info:
                    event_info['start_date'] = start_info['date']
                    event_info['all_day'] = True
                
                if 'dateTime' in end_info:
                    event_info['end_datetime'] = end_info['dateTime']
                    event_info['end_timezone'] = end_info.get('timeZone', 'UTC')
                elif 'date' in end_info:
                    event_info['end_date'] = end_info['date']
                
                # Handle attendees
                attendees = event.get('attendees', [])
                if attendees:
                    event_info['attendees'] = [
                        {
                            'email': attendee.get('email', ''),
                            'response_status': attendee.get('responseStatus', 'needsAction'),
                            'organizer': attendee.get('organizer', False)
                        }
                        for attendee in attendees
                    ]
                
                formatted_events.append(event_info)
            
            # Create summary
            summary = f"Found {len(events)} event(s) from {start_date} to {end_date}"
            if query:
                summary += f" matching query: '{query}'"
            
            result = {
                'summary': summary,
                'total_events': len(events),
                'events': formatted_events
            }
            
            return json.dumps(result, indent=2, default=str)
            
        except Exception as e:
            return f"Error searching events: {str(e)}"