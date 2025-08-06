#!/usr/bin/env python3
"""
Supabase Logging Service - Handles all activity logging to Supabase
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

class SupabaseLoggingService:
    """Service class for logging activities to Supabase"""
    
    def __init__(self):
        """Initialize the Supabase client"""
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    def log_activity(self, 
                    client_id: Optional[str] = None,
                    action: str = 'general',
                    description: str = '',
                    metadata: Optional[Dict[str, Any]] = None,
                    error_message: Optional[str] = None) -> bool:
        """
        Log an activity to Supabase
        
        Args:
            client_id: ID of the client (optional)
            action: Type of action being performed
            description: Human-readable description of the activity
            metadata: Additional data about the activity
            error_message: Error message if applicable
        
        Returns:
            bool: True if logging was successful, False otherwise
        """
        try:
            # Prepare the log entry
            log_entry = {
                'action': action,
                'description': description,
                'created_at': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            # Add optional fields
            if client_id:
                log_entry['client_id'] = client_id
            
            if error_message:
                log_entry['error_message'] = error_message
            
            # Insert the log entry
            result = self.client.table('activity_logs').insert(log_entry).execute()
            
            if result.data:
                print(f"✅ Logged activity: {action} - {description}")
                return True
            else:
                print(f"❌ Failed to log activity: {action}")
                return False
                
        except Exception as e:
            print(f"❌ Error logging activity: {e}")
            return False
    
    def log_client_interaction(self, 
                             client_id: str,
                             interaction_type: str,
                             description: str,
                             duration_minutes: Optional[int] = None,
                             topics: Optional[List[str]] = None) -> bool:
        """
        Log a client interaction
        
        Args:
            client_id: ID of the client
            interaction_type: Type of interaction (call, email, meeting, etc.)
            description: Description of the interaction
            duration_minutes: Duration in minutes (optional)
            topics: List of topics discussed (optional)
        
        Returns:
            bool: True if logging was successful, False otherwise
        """
        metadata = {
            'interaction_type': interaction_type,
            'duration_minutes': duration_minutes,
            'topics': topics or []
        }
        
        return self.log_activity(
            client_id=client_id,
            action='client_interaction',
            description=description,
            metadata=metadata
        )
    
    def log_document_creation(self, 
                            client_id: Optional[str],
                            document_type: str,
                            document_title: str,
                            document_url: Optional[str] = None,
                            folder_id: Optional[str] = None) -> bool:
        """
        Log document creation
        
        Args:
            client_id: ID of the client (optional)
            document_type: Type of document (IG Story, Template, etc.)
            document_title: Title of the document
            document_url: URL of the document (optional)
            folder_id: ID of the folder where document was created (optional)
        
        Returns:
            bool: True if logging was successful, False otherwise
        """
        metadata = {
            'document_type': document_type,
            'document_title': document_title,
            'document_url': document_url,
            'folder_id': folder_id
        }
        
        return self.log_activity(
            client_id=client_id,
            action='document_creation',
            description=f"Created {document_type}: {document_title}",
            metadata=metadata
        )
    
    def log_spreadsheet_update(self, 
                             spreadsheet_id: str,
                             sheet_name: str,
                             cell_ref: str,
                             action_type: str = 'cell_update') -> bool:
        """
        Log spreadsheet updates
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            sheet_name: Name of the sheet
            cell_ref: Cell reference (e.g., 'A1', 'E12')
            action_type: Type of action (cell_update, cell_insert, etc.)
        
        Returns:
            bool: True if logging was successful, False otherwise
        """
        metadata = {
            'spreadsheet_id': spreadsheet_id,
            'sheet_name': sheet_name,
            'cell_ref': cell_ref,
            'action_type': action_type
        }
        
        return self.log_activity(
            action='spreadsheet_update',
            description=f"Updated {sheet_name}!{cell_ref} in spreadsheet",
            metadata=metadata
        )
    
    def log_error(self, 
                 error_message: str,
                 action: str = 'general',
                 client_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log an error
        
        Args:
            error_message: The error message
            action: The action that caused the error
            client_id: ID of the client (optional)
            metadata: Additional error metadata (optional)
        
        Returns:
            bool: True if logging was successful, False otherwise
        """
        return self.log_activity(
            client_id=client_id,
            action=action,
            description=f"Error: {error_message}",
            error_message=error_message,
            metadata=metadata
        )
    
    def log_system_event(self, 
                        event_type: str,
                        description: str,
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Log a system event
        
        Args:
            event_type: Type of system event
            description: Description of the event
            metadata: Additional event metadata (optional)
        
        Returns:
            bool: True if logging was successful, False otherwise
        """
        return self.log_activity(
            action=event_type,
            description=description,
            metadata=metadata or {}
        )

# Convenience functions for quick access
def log_activity(client_id: Optional[str] = None,
                action: str = 'general',
                description: str = '',
                metadata: Optional[Dict[str, Any]] = None,
                error_message: Optional[str] = None) -> bool:
    """Quick function to log an activity"""
    try:
        service = SupabaseLoggingService()
        return service.log_activity(client_id, action, description, metadata, error_message)
    except Exception as e:
        print(f"❌ Error initializing logging service: {e}")
        return False

def log_client_interaction(client_id: str,
                          interaction_type: str,
                          description: str,
                          duration_minutes: Optional[int] = None,
                          topics: Optional[List[str]] = None) -> bool:
    """Quick function to log a client interaction"""
    try:
        service = SupabaseLoggingService()
        return service.log_client_interaction(client_id, interaction_type, description, duration_minutes, topics)
    except Exception as e:
        print(f"❌ Error logging client interaction: {e}")
        return False

def log_document_creation(client_id: Optional[str],
                         document_type: str,
                         document_title: str,
                         document_url: Optional[str] = None,
                         folder_id: Optional[str] = None) -> bool:
    """Quick function to log document creation"""
    try:
        service = SupabaseLoggingService()
        return service.log_document_creation(client_id, document_type, document_title, document_url, folder_id)
    except Exception as e:
        print(f"❌ Error logging document creation: {e}")
        return False

def log_error(error_message: str,
             action: str = 'general',
             client_id: Optional[str] = None,
             metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Quick function to log an error"""
    try:
        service = SupabaseLoggingService()
        return service.log_error(error_message, action, client_id, metadata)
    except Exception as e:
        print(f"❌ Error logging error: {e}")
        return False 