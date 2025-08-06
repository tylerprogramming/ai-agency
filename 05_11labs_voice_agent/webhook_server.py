import os
import time
import hmac
import hashlib
import base64
import json
from typing import Optional
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ElevenLabs Webhook Server", version="1.0.0")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your-webhook-secret-here")
TOLERANCE_SECONDS = 30 * 60 

class WebhookData(BaseModel):
    type: str
    data: dict
    event_timestamp: int

def verify_webhook_signature(request: Request, body: bytes) -> bool:
    """Verify the ElevenLabs webhook signature using HMAC."""
    signature_header = request.headers.get("elevenlabs-signature")
    if not signature_header:
        return False
    
    try:
        parts = signature_header.split(",")
        if len(parts) != 2:
            return False
        
        timestamp_str = parts[0].split("=")[1]
        hmac_signature = parts[1]
        
        # Validate timestamp (within tolerance)
        timestamp = int(timestamp_str)
        current_time = int(time.time())
        if abs(current_time - timestamp) > TOLERANCE_SECONDS:
            return False
        
        # Validate signature
        payload_to_sign = f"{timestamp}.{body.decode('utf-8')}"
        expected_signature = hmac.new(
            key=WEBHOOK_SECRET.encode("utf-8"),
            msg=payload_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        expected_header = f"v0={expected_signature}"
        return hmac_signature == expected_header
        
    except (ValueError, IndexError, KeyError):
        return False

def handle_transcription_webhook(data: dict):
    """Handle transcription webhook data."""
    print(f"📝 Transcription webhook received for conversation: {data.get('conversation_id')}")
    print(f"Agent ID: {data.get('agent_id')}")
    print(f"Status: {data.get('status')}")
    
    # Extract key information
    transcript = data.get('transcript', [])
    analysis = data.get('analysis', {})
    metadata = data.get('metadata', {})
    
    print(f"Transcript length: {len(transcript)} turns")
    if analysis:
        print(f"Call successful: {analysis.get('call_successful', 'N/A')}")
        print(f"Transcript summary: {analysis.get('transcript_summary', 'N/A')}")
    
    if metadata:
        print(f"Call duration: {metadata.get('duration_seconds', 'N/A')} seconds")
        print(f"Start time: {metadata.get('start_time_unix_secs', 'N/A')}")

def handle_audio_webhook(data: dict):
    """Handle audio webhook data."""
    print(f"🎵 Audio webhook received for conversation: {data.get('conversation_id')}")
    print(f"Agent ID: {data.get('agent_id')}")
    
    # Decode and save audio if needed
    full_audio = data.get('full_audio')
    if full_audio:
        try:
            audio_bytes = base64.b64decode(full_audio)
            conversation_id = data.get('conversation_id', 'unknown')
            filename = f"conversation_{conversation_id}.mp3"
            
            with open(filename, "wb") as f:
                f.write(audio_bytes)
            print(f"Audio saved as: {filename}")
        except Exception as e:
            print(f"Error saving audio: {e}")

@app.post("/post-call")
async def receive_webhook(request: Request):
    """Handle ElevenLabs post-call webhooks."""
    try:
        # Read the request body
        body = await request.body()
        
        # Verify webhook signature if secret is configured
        if WEBHOOK_SECRET != "your-webhook-secret-here":
            if not verify_webhook_signature(request, body):
                raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse the JSON payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")
        
        # Validate required fields
        if not isinstance(payload, dict) or 'type' not in payload:
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        webhook_type = payload.get('type')
        data = payload.get('data', {})
        
        print(f"🔔 Webhook received - Type: {webhook_type}")
        print(f"Event timestamp: {payload.get('event_timestamp', 'N/A')}")
        
        # Handle different webhook types
        if webhook_type == "post_call_transcription":
            handle_transcription_webhook(data)
        elif webhook_type == "post_call_audio":
            handle_audio_webhook(data)
        else:
            print(f"⚠️ Unknown webhook type: {webhook_type}")
        
        # Return 200 status code as required by ElevenLabs
        return JSONResponse(
            content={"status": "received", "type": webhook_type},
            status_code=200
        )
        
    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "service": "ElevenLabs Webhook Server",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/post-call",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting ElevenLabs webhook server on port {port}")
    print(f"📡 Webhook endpoint: http://localhost:{port}/post-call")
    print(f"🏥 Health check: http://localhost:{port}/health")
    
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=port) 