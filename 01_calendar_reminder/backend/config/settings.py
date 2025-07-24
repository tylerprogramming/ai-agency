import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App Configuration
    app_name: str = "Google Calendar API Backend"
    debug: bool = False
    
    # Server Configuration
    host: str = "localhost"
    port: int = 8000
    frontend_url: str = "http://localhost:3000"
    
    # CORS Configuration
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Google Calendar Configuration
    google_scopes: List[str] = ["https://www.googleapis.com/auth/calendar"]
    google_redirect_uri: str = "http://localhost:8000/auth/callback"
    
    # File Paths
    @property
    def client_secrets_file(self) -> str:
        return os.path.join(os.path.dirname(__file__), '../../calendar_credentials/client_secrets.json')
    
    @property
    def token_file(self) -> str:
        return os.path.join(os.path.dirname(__file__), '../../calendar_credentials/calendar_token.json')
    
    # Scheduler Configuration
    scheduler_timezone: str = "America/New_York"
    
    # API Keys (from environment)
    openai_api_key: str = ""
    serper_api_key: str = ""
    telegram_bot_token: str = ""
    
    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "../../.env")  # Look for .env at project root
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


    @classmethod
    def get_env_file_path(cls) -> str:
        """Get the expected path for the .env file"""
        return os.path.join(os.path.dirname(__file__), "../../.env")
    
    @classmethod
    def env_file_exists(cls) -> bool:
        """Check if the .env file exists"""
        return os.path.exists(cls.get_env_file_path())
    
    @classmethod
    def print_env_file_info(cls):
        """Print information about the .env file location"""
        env_path = cls.get_env_file_path()
        abs_path = os.path.abspath(env_path)
        exists = cls.env_file_exists()
        
        print(f"📁 .env file location: {abs_path}")
        print(f"✅ .env file exists: {'Yes' if exists else 'No'}")
        
        if not exists:
            print(f"\n💡 To create your .env file:")
            print(f"   1. Create a file called '.env' in: {os.path.dirname(abs_path)}")
            print(f"   2. Add your API keys and configuration")


# Create a global settings instance
settings = Settings()

# Print environment file info on startup (only in debug mode)
if settings.debug:
    Settings.print_env_file_info() 