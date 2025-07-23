from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config.settings import settings
from ..routers import auth, calendar, api
from ..services.scheduler_service import scheduler_service


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    
    app = FastAPI(
        title=settings.app_name,
        description="Google Calendar API Backend with AI-powered event parsing and scheduling",
        version="1.0.0",
        debug=settings.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=settings.cors_allow_methods,
        allow_headers=settings.cors_allow_headers,
    )

    # Include routers
    app.include_router(auth.router)
    app.include_router(calendar.router)
    app.include_router(api.router)

    # Root endpoint
    @app.get("/", tags=["root"])
    def read_root():
        return {"message": settings.app_name + " is running"}

    # Shutdown event to cleanup scheduler
    @app.on_event("shutdown")
    def shutdown_event():
        scheduler_service.shutdown()

    return app 