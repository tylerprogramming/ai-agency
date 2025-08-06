#!/usr/bin/env python3
"""
Simple startup script for the ElevenLabs webhook server.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting ElevenLabs webhook server on port {port}")
    print(f"📡 Webhook endpoint: http://localhost:{port}/post-call")
    print(f"🏥 Health check: http://localhost:{port}/health")
    print(f"📋 API docs: http://localhost:{port}/docs")
    
    # Use import string format for reload functionality
    uvicorn.run("webhook_server:app", host="0.0.0.0", port=port, reload=True) 