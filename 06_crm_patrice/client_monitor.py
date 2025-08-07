#!/usr/bin/env python3
"""
Optimized script to monitor for new clients that haven't been onboarded yet.
Uses APScheduler to run every minute.
"""

import os
from supabase import create_client, Client
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telegram_services.telegram import send_telegram_text_message
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from google_services.google_drive_services import GoogleDriveService
from database.logging_service import SupabaseLoggingService

# Load environment variables
load_dotenv()

DEFAULT_PROMPTS_DOC_ID = os.getenv("DEFAULT_PROMPTS_DOC_ID")
DEFAULT_TEMPLATES_DOC_ID = os.getenv("DEFAULT_TEMPLATES_DOC_ID")

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

logging_service = SupabaseLoggingService()

def check_new_clients():
    """Check for new clients that haven't been onboarded"""
    try:
        # Get clients that haven't been onboarded
        response = supabase.table('clients').select('*').eq('onboarded', False).execute()
        new_clients = response.data
        
        if not new_clients:
            print("No new clients need onboarding")
            return []
        
        print(f"Found {len(new_clients)} clients that need onboarding:")
        
        # Prepare notification message
        notification_parts = [f"🔔 NEW CLIENTS NEEDING ONBOARDING: {len(new_clients)}"]
        
        for client in new_clients:
            created_at = datetime.fromisoformat(client['created_at'].replace('Z', '+00:00'))
            time_since_created = datetime.now().astimezone() - created_at
            
            # Format time since created
            if time_since_created.days > 0:
                time_ago = f"{time_since_created.days} day{'s' if time_since_created.days != 1 else ''} ago"
            elif time_since_created.seconds >= 3600:
                hours = time_since_created.seconds // 3600
                time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                minutes = time_since_created.seconds // 60
                time_ago = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            
            print(f"  - {client['name']} ({client['email']}) - Created {time_ago}")
            notification_parts.append(f"👤 {client['name']} | {client['email']} | {time_ago}")
        
        # Send Telegram notification if there are new clients
        if new_clients:
            notification_message = "\n".join(notification_parts)
            send_telegram_text_message(notification_message)
            logging_service.log_activity(
                action="telegram_notification_sent",
                description=f"Sent notification for {len(new_clients)} new clients"
            )
        
        return new_clients
        
    except Exception as e:
        error_msg = f"Error checking for new clients: {e}"
        print(f"❌ {error_msg}")
        logging_service.log_error(error_msg, "client_monitoring")
        return []

def check_stale_clients(days_threshold=1):
    """Check for clients that were created X days ago but still not onboarded"""
    try:
        # Calculate the date threshold
        threshold_date = (datetime.now() - timedelta(days=days_threshold)).isoformat()
        
        response = supabase.table('clients').select('*').eq('onboarded', False).lt('created_at', threshold_date).execute()
        stale_clients = response.data
        
        if stale_clients:
            print(f"Found {len(stale_clients)} clients created >{days_threshold} day(s) ago that still need onboarding:")
            
            # Prepare notification message
            notification_parts = [f"⚠️ STALE CLIENTS NEEDING ATTENTION: {len(stale_clients)}"]
            
            for client in stale_clients:
                created_at = datetime.fromisoformat(client['created_at'].replace('Z', '+00:00'))
                days_old = (datetime.now().astimezone() - created_at).days
                
                print(f"  - {client['name']} ({client['email']}) - Created {days_old} days ago")
                notification_parts.append(f"⏰ {client['name']} | {client['email']} | {days_old} days old")
            
            # Send Telegram notification for stale clients
            notification_message = "\n".join(notification_parts)
            send_telegram_text_message(notification_message)
            logging_service.log_activity(
                action="telegram_notification_sent",
                description=f"Sent notification for {len(stale_clients)} stale clients"
            )
        
        return stale_clients
        
    except Exception as e:
        error_msg = f"Error checking for stale clients: {e}"
        print(f"❌ {error_msg}")
        logging_service.log_error(error_msg, "client_monitoring")
        return []

def mark_client_onboarded(client_id: str):
    """Mark a specific client as onboarded"""
    try:
        response = supabase.table('clients').update({'onboarded': True}).eq('id', client_id).execute()
        print(f"Marked client {client_id} as onboarded")
        logging_service.log_activity(
            action="client_onboarded",
            description=f"Marked client {client_id} as onboarded",
            client_id=client_id
        )
        return response.data
    except Exception as e:
        error_msg = f"Error marking client as onboarded: {e}"
        print(f"❌ {error_msg}")
        logging_service.log_error(error_msg, "client_onboarding", client_id=client_id)
        return None

def run_monitoring_check():
    """Main function to run the monitoring checks"""
    print("Starting client monitoring check...")

    new_clients = check_new_clients()
    stale_clients = check_stale_clients(days_threshold=1)

    total_pending = len(new_clients) + len(stale_clients)
    if total_pending > 0:
        print(f"Total clients pending onboarding: {total_pending}")
        
        # Initialize Google Drive service
        drive_service = GoogleDriveService()
        
        for client in new_clients:
            print(f"Creating Google Drive folder for client: {client['name']}")
            
            # Create folder for the client
            folder = drive_service.create_folder(f"Client - {client['name']}")
            
            if folder:
                print(f"✅ Created folder for {client['name']}: {folder.name} (ID: {folder.id})")
                print(f"🔗 Folder URL: {folder.url}")
                
                mark_client_onboarded(client['id'])
                
                logging_service.log_activity(
                    action="folder_created",
                    description=f"Created folder for {client['name']}: {folder.name}",
                    client_id=client['id'],
                    metadata={"folder_id": folder.id, "folder_url": folder.url}
                )

                # Copy default documents to the client's folder
                if DEFAULT_PROMPTS_DOC_ID:
                    prompts_doc = drive_service.copy_document(
                        document_id=DEFAULT_PROMPTS_DOC_ID,
                        new_name="Prompts",
                        destination_folder_id=folder.id
                    )
                    if prompts_doc:
                        print(f"✅ Copied prompts document: {prompts_doc.title} (ID: {prompts_doc.id})")
                        logging_service.log_document_creation(
                            client_id=client['id'],
                            document_type="Prompts Template",
                            document_title=prompts_doc.title,
                            document_url=prompts_doc.url,
                            folder_id=folder.id
                        )
                    else:
                        error_msg = f"Failed to copy prompts document for {client['name']}"
                        print(f"❌ {error_msg}")
                        logging_service.log_error(error_msg, "document_copy", client_id=client['id'])
                
                if DEFAULT_TEMPLATES_DOC_ID:
                    templates_doc = drive_service.copy_document(
                        document_id=DEFAULT_TEMPLATES_DOC_ID,
                        new_name="Templates",
                        destination_folder_id=folder.id
                    )
                    if templates_doc:
                        print(f"✅ Copied templates document: {templates_doc.title} (ID: {templates_doc.id})")
                        logging_service.log_document_creation(
                            client_id=client['id'],
                            document_type="Templates",
                            document_title=templates_doc.title,
                            document_url=templates_doc.url,
                            folder_id=folder.id
                        )
                    else:
                        error_msg = f"Failed to copy templates document for {client['name']}"
                        print(f"❌ {error_msg}")
                        logging_service.log_error(error_msg, "document_copy", client_id=client['id'])
                
                # Create a welcome document
                welcome_doc = drive_service.create_text_document(
                    title=f"Welcome - {client['name']}",
                    content=f"Welcome {client['name']}! We're excited to work with you.\n\nThis folder contains your personalized prompts and templates to help you get started.",
                    folder_id=folder.id
                )
                if welcome_doc:
                    print(f"✅ Created welcome document: {welcome_doc.title} (ID: {welcome_doc.id})")
                    logging_service.log_document_creation(
                        client_id=client['id'],
                        document_type="Welcome Document",
                        document_title=welcome_doc.title,
                        document_url=welcome_doc.url,
                        folder_id=folder.id
                    )
                else:
                    error_msg = f"Failed to create welcome document for {client['name']}"
                    print(f"❌ {error_msg}")
                    logging_service.log_error(error_msg, "document_creation", client_id=client['id'])
                
            else:
                error_msg = f"Failed to create folder for client: {client['name']}"
                print(f"❌ {error_msg}")
                logging_service.log_error(error_msg, "folder_creation", client_id=client['id'])
        
    else:
        print("All clients are up to date!")
    
    return {
        'new_clients': new_clients,
        'stale_clients': stale_clients,
        'total_pending': total_pending
    }

def start_scheduler():
    """Start the APScheduler to run monitoring every minute"""
    scheduler = BlockingScheduler()
    
    # Add the job to run every minute
    scheduler.add_job(
        func=run_monitoring_check,
        trigger=IntervalTrigger(minutes=1),
        id='client_monitoring',
        name='Check for new clients every minute',
        replace_existing=True
    )
    
    print("Starting APScheduler - monitoring clients every minute...")
    print("Press Ctrl+C to stop the scheduler")
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Scheduler stopped by user")
        scheduler.shutdown()

if __name__ == "__main__":
    # Check if running as a one-time check or as a scheduler
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run once and exit
        run_monitoring_check()
    else:
        # Run as a scheduler
        start_scheduler() 