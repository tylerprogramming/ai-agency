import os
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from typing import Optional

from ..config.settings import settings


class AuthService:
    def __init__(self):
        self.client_secrets_file = settings.client_secrets_file
        self.scopes = settings.google_scopes
        self.redirect_uri = settings.google_redirect_uri
        self.token_file = settings.token_file

    def create_auth_flow(self) -> Flow:
        """Create Google OAuth flow"""
        return Flow.from_client_secrets_file(
            self.client_secrets_file,
            scopes=self.scopes,
            redirect_uri=self.redirect_uri
        )

    def get_auth_url(self) -> str:
        """Get authorization URL for OAuth flow"""
        flow = self.create_auth_flow()
        auth_url, _ = flow.authorization_url(prompt='consent')
        return auth_url

    def handle_callback(self, code: str) -> Credentials:
        """Handle OAuth callback and save credentials"""
        flow = self.create_auth_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        # Save token for later use
        with open(self.token_file, 'w') as token:
            token.write(creds.to_json())
        
        return creds

    def get_valid_credentials(self) -> Optional[Credentials]:
        """Get valid credentials, refreshing if necessary"""
        if not os.path.exists(self.token_file):
            return None
        
        creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        
        # If credentials are expired, refresh them
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
            # Save refreshed credentials
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        return creds if creds and creds.valid else None

    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.get_valid_credentials() is not None

    def logout(self) -> bool:
        """Log out user by removing token file"""
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            return True
        return False


# Create a global auth service instance
auth_service = AuthService() 