"""
Google Calendar API Backend

A modular FastAPI application for managing Google Calendar events with AI-powered features.
Includes authentication, calendar management, AI text parsing, and scheduled reminders.
"""

from .core.app import create_app

# Create the FastAPI app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    from .config.settings import settings
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )