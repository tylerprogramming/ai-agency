from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..models.schemas import (
    ChatRequest, ChatResponse, ParseTextRequest, ParseTextResponse,
    DailyScheduleResponse, TelegramRequest, TelegramTestRequest,
    ScheduleReminderRequest, ReminderStatusResponse, TestScheduleRequest, TestScheduleResponse
)
from ..services.auth_service import auth_service
from ..services.calendar_service import calendar_service
from ..services.scheduler_service import scheduler_service
from ..services.ai_service import ai_service
from ..telegram import send_telegram_text_message
from ..config.settings import settings, Settings

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/config/env-info")
def get_env_info():
    """Get information about the .env file location and status"""
    import os
    env_path = Settings.get_env_file_path()
    abs_path = os.path.abspath(env_path)
    exists = Settings.env_file_exists()
    
    return {
        "env_file_path": abs_path,
        "env_file_exists": exists,
        "project_root": os.path.dirname(abs_path),
        "instructions": {
            "step_1": f"Create a file called '.env' in: {os.path.dirname(abs_path)}",
            "step_2": "Add your API keys and configuration to the .env file",
            "example_content": """# API Keys
OPENAI_API_KEY=your_openai_api_key_here
SERPER_API_KEY=your_serper_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Optional Settings
DEBUG=false
HOST=localhost
PORT=8000"""
        }
    }


@router.post("/chat/stream", response_model=ChatResponse)
async def chat_stream(request: ChatRequest):
    """Chat with calendar assistant"""
    try:
        if not request.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is not set. Please add it in settings.")
        
        response = ai_service.chat_with_calendar(
            [msg.dict() for msg in request.messages], 
            request.openai_api_key
        )
        
        return ChatResponse(response=response)
        
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Error processing chat request")


@router.post("/parse-text-to-events", response_model=ParseTextResponse)
async def parse_text_to_events(request: ParseTextRequest):
    """Parse free-form text and create calendar events using CrewAI agents"""
    try:
        if not request.text.strip():
            raise HTTPException(status_code=400, detail="Text input is required")
        
        if not request.openai_api_key:
            raise HTTPException(status_code=400, detail="OpenAI API key is required")
        
        # Check authentication
        if not auth_service.is_authenticated():
            raise HTTPException(status_code=401, detail="User not authenticated with Google Calendar")
        
        # Parse events using AI
        events_data = ai_service.parse_text_to_events(request.text, request.openai_api_key)
        
        if not events_data:
            return ParseTextResponse(
                message="No events were identified in the provided text",
                events_created=0,
                events_failed=0,
                created_events=[],
                failed_events=[],
                parsed_text=request.text
            )
        
        # Create events
        result = ai_service.create_events_from_parsed_data(events_data)
        
        return ParseTextResponse(
            message=f"Successfully created {len(result['created_events'])} event(s) from text",
            events_created=len(result['created_events']),
            events_failed=len(result['failed_events']),
            created_events=result['created_events'],
            failed_events=result['failed_events'],
            parsed_text=request.text
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in parse_text_to_events: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/daily-schedule", response_model=DailyScheduleResponse)
def get_daily_schedule():
    """Get formatted daily schedule"""
    events = calendar_service.get_today_events()
    formatted_message = scheduler_service.format_daily_schedule(events)
    return DailyScheduleResponse(message=formatted_message, events_count=len(events))


@router.get("/daily-schedule/{date}", response_model=DailyScheduleResponse)
def get_daily_schedule_for_date(date: str):
    """Get formatted daily schedule for a specific date (YYYY-MM-DD)"""
    try:
        events = calendar_service.get_events_for_date(date)
        formatted_message = scheduler_service.format_daily_schedule(events)
        return DailyScheduleResponse(
            message=formatted_message, 
            events_count=len(events), 
            date=date
        )
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-daily-telegram")
async def send_daily_telegram(request: TelegramRequest):
    """Send daily schedule via Telegram"""
    try:
        if not request.bot_token or not request.chat_id:
            raise HTTPException(status_code=400, detail="Bot token and chat ID are required")
        
        events = calendar_service.get_today_events()
        message = scheduler_service.format_daily_schedule(events)
        
        success = send_telegram_text_message(message, request.bot_token, request.chat_id)
        
        if success:
            return {"message": "Daily schedule sent successfully", "events_count": len(events)}
        else:
            raise HTTPException(status_code=500, detail="Failed to send Telegram message")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-telegram")
async def test_telegram(request: TelegramTestRequest):
    """Test Telegram connection"""
    try:
        if not request.bot_token or not request.chat_id:
            raise HTTPException(status_code=400, detail="Bot token and chat ID are required")
        
        test_message = "🤖 Test message from Calendar Reminder Bot!\n\nYour Telegram integration is working correctly."
        success = send_telegram_text_message(test_message, request.bot_token, request.chat_id)
        
        if success:
            return {"message": "Test message sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test message")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule-daily-reminder")
async def schedule_daily_reminder(request: ScheduleReminderRequest):
    """Schedule or update daily reminder"""
    try:
        if not request.bot_token or not request.chat_id:
            raise HTTPException(status_code=400, detail="Bot token and chat ID are required")
        
        result = scheduler_service.schedule_daily_reminder(
            request.bot_token, 
            request.chat_id, 
            request.hour, 
            request.minute, 
            request.enabled, 
            request.user_id
        )
        
        return result
        
    except Exception as e:
        print(f"Error scheduling reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reminder-status", response_model=ReminderStatusResponse)
def get_reminder_status():
    """Get current reminder status"""
    try:
        result = scheduler_service.get_reminder_status()
        return ReminderStatusResponse(**result)
        
    except Exception as e:
        print(f"Error getting reminder status: {e}")
        return ReminderStatusResponse(
            scheduled=False, 
            enabled=False, 
            user_id="default_user", 
            error=str(e)
        )


@router.delete("/cancel-daily-reminder")
def cancel_daily_reminder():
    """Cancel daily reminder"""
    try:
        result = scheduler_service.cancel_daily_reminder()
        return result
        
    except Exception as e:
        print(f"Error cancelling reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-schedule", response_model=TestScheduleResponse)
async def test_schedule(request: TestScheduleRequest):
    """Schedule a test reminder in 1 minute for testing"""
    try:
        if not request.bot_token or not request.chat_id:
            raise HTTPException(status_code=400, detail="Bot token and chat ID are required")
        
        result = scheduler_service.schedule_test_reminder(request.bot_token, request.chat_id)
        return TestScheduleResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 