from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List

from ..models.schemas import AuthStatus, CreateEventRequest, DailyScheduleResponse
from ..services.auth_service import auth_service
from ..services.calendar_service import calendar_service

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/authenticated", response_model=AuthStatus)
def calendar_authenticated():
    """Check if user is authenticated - alias for auth_status"""
    return AuthStatus(authenticated=auth_service.is_authenticated())


@router.get("/events")
def get_calendar_events():
    """Get current month's calendar events"""
    if not auth_service.is_authenticated():
        raise HTTPException(status_code=401, detail="User not authenticated.")
    
    events = calendar_service.get_current_month_events()
    return JSONResponse(content=events)


@router.post("/add")
async def add_calendar_event(event_request: CreateEventRequest):
    """Add a new calendar event"""
    if not auth_service.is_authenticated():
        raise HTTPException(status_code=401, detail="User not authenticated.")
    
    try:
        created_event = calendar_service.create_event(event_request)
        return JSONResponse(content=created_event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 