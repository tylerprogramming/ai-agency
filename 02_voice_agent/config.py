"""Configuration management for the Voice Agent application."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class VoiceAgentConfig:
    """Configuration settings for the Voice Agent application."""
    
    # API Keys
    openai_api_key: str
    firecrawl_api_key: str
    elevenlabs_api_key: str
    
    # ElevenLabs Configuration
    elevenlabs_voice_id: str
    
    # Telegram Configuration
    telegram_bot_token: str
    telegram_chat_id: str
    
    # Application Configuration
    search_limit: int = 5
    search_time_filter: str = "qdr:d"  # Last day
    openai_model: str = "gpt-4.1"
    elevenlabs_model: str = "eleven_multilingual_v2"
    audio_format: str = "mp3_44100_128"
    
    @classmethod
    def from_environment(cls) -> "VoiceAgentConfig":
        """Create configuration from environment variables."""
        required_env_vars = {
            "OPENAI_API_KEY": "OpenAI API key",
            "FIRECRAWL_API_KEY": "Firecrawl API key", 
            "ELEVENLABS_API_KEY": "ElevenLabs API key",
            "ELEVENLABS_VOICE_ID": "ElevenLabs voice ID",
            "TELEGRAM_BOT_TOKEN": "Telegram bot token",
            "TELEGRAM_CHAT_ID": "Telegram chat ID"
        }
        
        missing_vars = []
        for env_var, description in required_env_vars.items():
            if not os.getenv(env_var):
                missing_vars.append(f"{env_var} ({description})")
        
        if missing_vars:
            raise ValueError(
                f"Missing required environment variables:\n" + 
                "\n".join(f"- {var}" for var in missing_vars)
            )
        
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            firecrawl_api_key=os.getenv("FIRECRAWL_API_KEY", ""),
            elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY", ""),
            elevenlabs_voice_id=os.getenv("ELEVENLABS_VOICE_ID", ""),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            search_limit=int(os.getenv("SEARCH_LIMIT", "5")),
            search_time_filter=os.getenv("SEARCH_TIME_FILTER", "qdr:d"),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
            elevenlabs_model=os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2"),
            audio_format=os.getenv("AUDIO_FORMAT", "mp3_44100_128")
        )
    
    def validate(self) -> None:
        """Validate the configuration."""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required")
        if not self.firecrawl_api_key:
            raise ValueError("Firecrawl API key is required")
        if not self.elevenlabs_api_key:
            raise ValueError("ElevenLabs API key is required")
        if not self.telegram_bot_token:
            raise ValueError("Telegram bot token is required")
        if not self.telegram_chat_id:
            raise ValueError("Telegram chat ID is required") 