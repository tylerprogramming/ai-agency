from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from .calendar_service import calendar_service
from ..telegram import send_telegram_text_message
from ..config.settings import settings


class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=pytz.timezone(settings.scheduler_timezone))
        self.scheduled_reminders: Dict[str, Dict[str, Any]] = {}
        self.scheduler.start()

    def format_daily_schedule(self, events) -> str:
        """Format today's events into a readable message"""
        eastern = pytz.timezone('America/New_York')
        today = datetime.now(eastern).strftime('%A, %B %d, %Y')
        
        if not events:
            return f"📅 **Schedule for {today}**\n\n🎉 No events scheduled for today! Enjoy your free day."
        
        message = f"📅 **Your Schedule for {today}**\n\n"
        
        for event in events:
            title = event.get('summary', 'Untitled Event')
            
            # Handle all-day events
            if 'date' in event.get('start', {}):
                message += f"🗓️ **{title}** (All day)\n"
            else:
                # Handle timed events
                start_time = event.get('start', {}).get('dateTime', '')
                if start_time:
                    # Parse and format time in Eastern timezone
                    from datetime import timezone
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=timezone.utc)
                    eastern_time = start_dt.astimezone(eastern)
                    time_str = eastern_time.strftime('%I:%M %p')
                    message += f"⏰ **{time_str}** - {title}\n"
            
            # Add location if available
            if event.get('location'):
                message += f"   📍 {event['location']}\n"
            
            message += "\n"
        
        message += f"Have a great day! 🌟"
        return message

    def send_scheduled_reminder(self, bot_token: str, chat_id: str, user_id: str):
        """Function called by scheduler to send daily reminders"""
        try:
            print(f"Sending scheduled reminder for user {user_id} at {datetime.now()}")
            events = calendar_service.get_today_events()
            message = self.format_daily_schedule(events)
            success = send_telegram_text_message(message, bot_token, chat_id)
            
            if success:
                print(f"✅ Scheduled reminder sent successfully to {chat_id}")
            else:
                print(f"❌ Failed to send scheduled reminder to {chat_id}")
                
        except Exception as e:
            print(f"Error in scheduled reminder: {e}")

    def schedule_daily_reminder(self, bot_token: str, chat_id: str, hour: int = 9, 
                               minute: int = 0, enabled: bool = True, user_id: str = "default_user") -> Dict[str, Any]:
        """Schedule or update daily reminder"""
        job_id = f"daily_reminder_{user_id}"
        
        # Remove existing job if it exists
        if job_id in self.scheduled_reminders:
            self.scheduler.remove_job(job_id)
            del self.scheduled_reminders[job_id]
            print(f"Removed existing reminder for user {user_id}")
        
        if enabled:
            # Schedule new job
            trigger = CronTrigger(hour=hour, minute=minute, timezone=pytz.timezone(settings.scheduler_timezone))
            job = self.scheduler.add_job(
                self.send_scheduled_reminder,
                trigger=trigger,
                args=[bot_token, chat_id, user_id],
                id=job_id,
                replace_existing=True
            )
            
            # Store reminder info
            self.scheduled_reminders[job_id] = {
                "user_id": user_id,
                "bot_token": bot_token,
                "chat_id": chat_id,
                "hour": hour,
                "minute": minute,
                "enabled": True,
                "job_id": job_id
            }
            
            next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            print(f"Scheduled daily reminder for user {user_id} at {hour:02d}:{minute:02d}. Next run: {next_run}")
            
            return {
                "message": f"Daily reminder scheduled for {hour:02d}:{minute:02d} Eastern Time",
                "next_run": next_run,
                "enabled": True
            }
        else:
            return {"message": "Daily reminder disabled", "enabled": False}

    def get_reminder_status(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Get current reminder status"""
        job_id = f"daily_reminder_{user_id}"
        
        if job_id in self.scheduled_reminders:
            reminder = self.scheduled_reminders[job_id]
            job = self.scheduler.get_job(job_id)
            
            if job:
                next_run = job.next_run_time.strftime('%Y-%m-%d %H:%M:%S %Z') if job.next_run_time else None
                return {
                    "scheduled": True,
                    "enabled": reminder["enabled"],
                    "hour": reminder["hour"],
                    "minute": reminder["minute"],
                    "next_run": next_run,
                    "user_id": user_id
                }
        
        return {"scheduled": False, "enabled": False, "user_id": user_id}

    def cancel_daily_reminder(self, user_id: str = "default_user") -> Dict[str, Any]:
        """Cancel daily reminder"""
        job_id = f"daily_reminder_{user_id}"
        
        if job_id in self.scheduled_reminders:
            self.scheduler.remove_job(job_id)
            del self.scheduled_reminders[job_id]
            print(f"Cancelled daily reminder for user {user_id}")
            return {"message": "Daily reminder cancelled", "cancelled": True}
        else:
            return {"message": "No reminder was scheduled", "cancelled": False}

    def schedule_test_reminder(self, bot_token: str, chat_id: str) -> Dict[str, str]:
        """Schedule a test reminder in 1 minute for testing"""
        test_time = datetime.now() + timedelta(minutes=1)
        
        job_id = "test_reminder"
        self.scheduler.add_job(
            self.send_scheduled_reminder,
            'date',
            run_date=test_time,
            args=[bot_token, chat_id, "test_user"],
            id=job_id,
            replace_existing=True
        )
        
        return {
            "message": f"Test reminder scheduled for {test_time.strftime('%H:%M:%S')}",
            "scheduled_time": test_time.isoformat()
        }

    def shutdown(self):
        """Shutdown scheduler"""
        self.scheduler.shutdown()


# Create a global scheduler service instance
scheduler_service = SchedulerService() 