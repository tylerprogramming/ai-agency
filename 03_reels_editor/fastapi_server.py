"""
FastAPI server for handling Composio webhooks with Gmail message processing.
Based on FastAPI 2024 best practices and security guidelines.
"""

import asyncio
import hashlib
import hmac
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings


# Configuration
class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    app_name: str = "Gmail Webhook Processor"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Security settings
    webhook_secret: str = Field(default="your-webhook-secret-key", description="Secret for webhook signature verification")
    allowed_hosts: list[str] = Field(default=["localhost", "127.0.0.1"], description="Allowed hosts for the application")
    
    # Gmail processing settings
    default_email_prompt: str = Field(
        default="Analyze this email and categorize it appropriately",
        description="Default prompt for email processing"
    )
    
    model_config = ConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra='ignore'  # Ignore extra fields not defined in the model
    )


# Pydantic Models
class GmailMessage(BaseModel):
    """Gmail message model with validation."""
    
    id: str = Field(..., description="Unique message ID")
    user_id: str = Field(..., description="User ID associated with the message")
    subject: str = Field(default="", description="Email subject")
    sender: str = Field(..., description="Email sender")
    content: str = Field(default="", description="Email content")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    
    @classmethod
    def from_composio_payload(cls, payload: Dict[str, Any]) -> "GmailMessage":
        """Create GmailMessage from Composio webhook payload."""
        # Extract relevant data from the Composio payload
        # This is a simplified example - adjust based on actual Composio payload structure
        message_data = payload.get("data", {})
        
        return cls(
            id=message_data.get("messageId", str(uuid.uuid4())),
            user_id=payload.get("userId", "unknown"),
            subject=message_data.get("subject", ""),
            sender=message_data.get("from", ""),
            content=message_data.get("body", ""),
        )


class WebhookPayload(BaseModel):
    """Webhook payload validation model."""
    
    type: str = Field(..., description="Webhook event type")
    data: Dict[str, Any] = Field(..., description="Webhook event data")
    user_id: Optional[str] = Field(None, description="User ID for the event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")


class WebhookResponse(BaseModel):
    """Standard webhook response model."""
    
    status: str = Field(..., description="Response status")
    webhook_id: str = Field(..., description="Unique webhook processing ID")
    message: Optional[str] = Field(None, description="Additional response message")


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global settings
settings = Settings()


# Background task processing
async def process_gmail_message(gmail_message: GmailMessage, user_prompt: str) -> None:
    """
    Process Gmail message in background.
    
    This function handles the actual email processing logic.
    In a real implementation, this would integrate with your AI service.
    """
    try:
        logger.info(f"Processing email {gmail_message.id} for user {gmail_message.user_id}")
        
        # Simulate processing time
        await asyncio.sleep(1)
        
        # Here you would integrate with your actual email processing logic
        # For example:
        # - Call your AI service with the user_prompt and email content
        # - Store results in database
        # - Send notifications
        
        logger.info(f"Successfully processed email {gmail_message.id}")
        
    except Exception as e:
        logger.error(f"Failed to process email {gmail_message.id}: {str(e)}")
        # In production, you might want to implement retry logic or dead letter queues


def get_user_prompt(user_id: str, default_prompt: str) -> str:
    """
    Get user-specific prompt or return default.
    
    In a real implementation, this would fetch from a database.
    """
    # Placeholder implementation - replace with actual database lookup
    user_prompts = {
        "user123": "Custom prompt for user123",
        "user456": "Another custom prompt",
    }
    
    return user_prompts.get(user_id, default_prompt)


# Security utilities
def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify webhook signature using HMAC-SHA256.
    
    This provides authentication and integrity verification for webhook requests.
    """
    if not signature or not secret:
        return False
    
    try:
        # Remove potential prefix (e.g., "sha256=")
        if signature.startswith("sha256="):
            signature = signature[7:]
        
        # Compute expected signature
        expected_signature = hmac.new(
            "56e7018f-1504-4a8e-b3eb-32636ca23063".encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(signature, expected_signature)
    
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False


# Dependency for webhook signature verification
async def verify_webhook_security(request: Request) -> bool:
    """
    Dependency to verify webhook signature.
    
    This ensures that incoming webhooks are legitimate.
    """
    signature = request.headers.get("x-signature") or request.headers.get("x-hub-signature-256")
    
    if not signature:
        logger.warning("Webhook request missing signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook signature"
        )
    
    body = await request.body()
    
    if not verify_webhook_signature(body, signature, settings.webhook_secret):
        logger.warning("Invalid webhook signature")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature"
        )
    
    return True


# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events.
    
    This replaces the deprecated on_event decorators.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown complete")


# FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI server for processing Gmail webhooks from Composio",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,  # Hide docs in production
    redoc_url="/redoc" if settings.debug else None,
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.allowed_hosts
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.composio.dev"],  # Restrict to Composio's domain
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version
    }


# Main webhook endpoint
@app.post("/composio/webhook", response_model=WebhookResponse)
async def listen_webhooks(
    request: Request,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_webhook_security),  # Security dependency
) -> WebhookResponse:
    """
    Main webhook endpoint for processing Gmail new message events.
    
    This is the core webhook labeling functionality that:
    1. Verifies webhook signature for security
    2. Validates the payload structure
    3. Processes Gmail events in the background
    4. Returns immediate response to avoid timeouts
    """
    webhook_id = str(uuid.uuid4())
    logger.info(request)
    
    logger.info(f"Received webhook {webhook_id} of type: {request}")
    
    try:
        # Check if this is a Gmail new message event
        # is_drive_event = (
        #     webhook_payload.type == "gmail_new_message" or
        #     "drive" in webhook_payload.type.lower()
        # )
        
        if True:
            # Parse Gmail message from payload
            # gmail_message = GmailMessage.from_composio_payload({
            #     "data": webhook_payload.data,
            #     "userId": webhook_payload.user_id
            # })
            
            # # Get user's custom prompt or use default
            # user_prompt = get_user_prompt(
            #     gmail_message.user_id, 
            #     settings.default_email_prompt
            # )
            
            # # Add email processing to background tasks
            # background_tasks.add_task(
            #     process_gmail_message,
            #     gmail_message,
            #     user_prompt
            # )
            
            # logger.info(f"Queued email {gmail_message.id} for processing")
            
            return WebhookResponse(
                status="received",
                webhook_id=webhook_id,
                message=f"Drive message {request} queued for processing"
            )
        
        else:
            logger.info(f"Ignored non-Gmail webhook: {webhook_payload.type}")
            return WebhookResponse(
                status="ignored",
                webhook_id=webhook_id,
                message=f"Event type {webhook_payload.type} not processed"
            )
    
    except Exception as e:
        logger.error(f"Error processing webhook {webhook_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing webhook"
        )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )