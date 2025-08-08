#!/usr/bin/env python3
"""
DocumentProvisioner - copy default content docs into a client's Google Drive folder
"""

from typing import Optional
from google_services.google_drive_services import GoogleDriveService
from database.logging_service import SupabaseLoggingService
from config import Config


class DocumentProvisioner:
    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config()
        self.drive = GoogleDriveService()
        self.logger = SupabaseLoggingService()

    def provision_default_documents(self, client: dict, folder_id: str) -> None:
        """Copy configured default docs (blog, webinar, instagram, email) into folder_id.
        client: dict should include 'id' and 'name'.
        """
        mappings = [
            (self.config.DEFAULT_BLOG_DOC_ID, "Blog"),
            (self.config.DEFAULT_WEBINAR_DOC_ID, "Webinar"),
            (self.config.DEFAULT_INSTAGRAM_DOC_ID, "Instagram"),
            (self.config.DEFAULT_EMAIL_DOC_ID, "Email"),
        ]

        for doc_id, new_name in mappings:
            if not doc_id:
                continue
            try:
                copied = self.drive.copy_document(
                    document_id=doc_id,
                    new_name=new_name,
                    destination_folder_id=folder_id,
                )
                if copied:
                    print(f"✅ Copied {new_name} doc: {copied.title} (ID: {copied.id})")
                    self.logger.log_document_creation(
                        client_id=client.get('id'),
                        document_type=new_name,
                        document_title=copied.title,
                        document_url=copied.url,
                        folder_id=folder_id,
                    )
                else:
                    error_msg = f"Failed to copy {new_name} document for {client.get('name')}"
                    print(f"❌ {error_msg}")
                    self.logger.log_error(error_msg, "document_copy", client_id=client.get('id'))
            except Exception as e:
                print(f"❌ Error copying {new_name} for {client.get('name')}: {e}")
                self.logger.log_error(str(e), "document_copy", client_id=client.get('id'))

