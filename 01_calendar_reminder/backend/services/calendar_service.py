from googleapiclient.discovery import build
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pytz

from .auth_service import auth_service
from ..models.schemas import CalendarEvent, CreateEventRequest


class CalendarService:
    def __init__(self):
        self.auth_service = auth_service

    def _get_service(self):
        """Get authenticated Google Calendar service"""
        creds = self.auth_service.get_valid_credentials()
        if not creds:
            raise ValueError("User not authenticated")
        return build('calendar', 'v3', credentials=creds)

    def get_current_month_events(self) -> List[Dict[str, Any]]:
        """Get events from the past year to the future year"""
        service = self._get_service()
        
        now = datetime.utcnow()
        # Get events from 1 year ago to 1 year in the future
        start_time = (now - timedelta(days=365)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = (now + timedelta(days=365)).replace(hour=23, minute=59, second=59, microsecond=999999)
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_time.isoformat() + 'Z',
            timeMax=end_time.isoformat() + 'Z',
            maxResults=2500,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return events_result.get('items', [])

    def get_today_events(self) -> List[Dict[str, Any]]:
        """Get today's calendar events"""
        creds = self.auth_service.get_valid_credentials()
        if not creds:
            return []
        
        service = self._get_service()
        
        # Use Eastern timezone since your events are in America/New_York
        eastern = pytz.timezone('America/New_York')
        today = datetime.now(eastern)
        
        # Start and end of day in Eastern time
        start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        try:
            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Filter events that are actually today (in case of timezone edge cases)
            today_events = []
            for event in events:
                event_start = event.get('start', {})
                
                # Handle all-day events
                if 'date' in event_start:
                    event_date = datetime.strptime(event_start['date'], '%Y-%m-%d').date()
                    if event_date == today.date():
                        today_events.append(event)
                else:
                    # Handle timed events
                    if 'dateTime' in event_start:
                        event_dt = datetime.fromisoformat(event_start['dateTime'].replace('Z', '+00:00'))
                        # Convert to Eastern time for comparison
                        if event_dt.tzinfo is None:
                            from datetime import timezone
                            event_dt = event_dt.replace(tzinfo=timezone.utc)
                        event_eastern = event_dt.astimezone(eastern)
                        
                        if event_eastern.date() == today.date():
                            today_events.append(event)
            
            return today_events
            
        except Exception as e:
            print(f"Error fetching today's events: {e}")
            return []

    def get_events_for_date(self, date: str) -> List[Dict[str, Any]]:
        """Get events for a specific date (YYYY-MM-DD)"""
        import pytz
        from datetime import timezone
        
        eastern = pytz.timezone('America/New_York')
        target_date = datetime.strptime(date, '%Y-%m-%d')
        target_date_eastern = eastern.localize(target_date)
        
        start_of_day = target_date_eastern.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = target_date_eastern.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        service = self._get_service()
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_of_day.isoformat(),
            timeMax=end_of_day.isoformat(),
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Filter events for the specific date
        date_events = []
        for event in events:
            event_start = event.get('start', {})
            
            if 'date' in event_start:
                event_date = datetime.strptime(event_start['date'], '%Y-%m-%d').date()
                if event_date == target_date.date():
                    date_events.append(event)
            elif 'dateTime' in event_start:
                event_dt = datetime.fromisoformat(event_start['dateTime'].replace('Z', '+00:00'))
                if event_dt.tzinfo is None:
                    event_dt = event_dt.replace(tzinfo=timezone.utc)
                event_eastern = event_dt.astimezone(eastern)
                
                if event_eastern.date() == target_date.date():
                    date_events.append(event)
        
        return date_events

    def create_event(self, event_request: CreateEventRequest) -> Dict[str, Any]:
        """Create a new calendar event"""
        service = self._get_service()
        
        event = {
            'summary': event_request.title,
            'description': event_request.description,
            'start': {'dateTime': event_request.start, 'timeZone': 'UTC'},
            'end': {'dateTime': event_request.end, 'timeZone': 'UTC'},
        }
        
        if event_request.location:
            event['location'] = event_request.location
        
        if event_request.attendees:
            event['attendees'] = [{'email': email} for email in event_request.attendees]
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return created_event


# Create a global calendar service instance
calendar_service = CalendarService() 