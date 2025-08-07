#!/usr/bin/env python3
"""
Google Drive Services - Methods for creating and managing Google Drive documents
"""

import os
from typing import Optional
from .google_sheets_auth import GoogleSheetsAuth
from googleapiclient.discovery import build
from dotenv import load_dotenv
from .models import GoogleDriveFolder, GoogleDriveDocument, GoogleDriveFile
from typing import Optional

# Load environment variables
load_dotenv()


class GoogleDriveService:
    """Service class for Google Drive operations"""
    
    def __init__(self, credentials_path="credentials/client_secrets.json"):
        """Initialize the service with credentials"""
        self.auth = GoogleSheetsAuth(credentials_path)
        # Get credentials with Drive scope
        self.credentials = self.auth.get_credentials(scopes=[
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file'
        ])
        self.service = build('drive', 'v3', credentials=self.credentials)
    
    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> Optional[GoogleDriveFolder]:
        """
        Create a new folder in Google Drive
        
        Args:
            folder_name: The name of the folder to create
            parent_folder_id: Google Drive folder ID to create the folder in (optional)
                            If not provided, will use GOOGLE_DRIVE_ROOT_FOLDER_ID from .env
        
        Returns:
            GoogleDriveFolder object or None if error
        """
        try:
            # If no parent_folder_id provided, try to get from environment variable
            if not parent_folder_id:
                parent_folder_id = os.getenv('GOOGLE_DRIVE_ROOT_FOLDER_ID')
                if not parent_folder_id:
                    print("⚠️ No parent folder ID provided and GOOGLE_DRIVE_ROOT_FOLDER_ID not set in .env")
            
            # Create the folder metadata
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            # If parent_folder_id is specified, add it to parents
            if parent_folder_id:
                folder_metadata['parents'] = [parent_folder_id]
            
            # Create the folder
            folder = self.service.files().create(
                body=folder_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            print(f"✅ Created folder: {folder_name} (ID: {folder['id']})")
            
            # Return Pydantic model
            return GoogleDriveFolder(
                id=folder['id'],
                name=folder['name'],
                url=folder['webViewLink']
            )
            
        except Exception as e:
            print(f"❌ Error creating folder: {e}")
            return None
    
    def create_text_document(self, title: str, content: str = "", folder_id: str = None) -> Optional[GoogleDriveDocument]:
        """
        Create a new Google Doc with text content
        
        Args:
            title: The title/name of the document
            content: Initial text content (optional)
            folder_id: Google Drive folder ID to create the doc in (optional)
        
        Returns:
            GoogleDriveDocument object or None if error
        """
        try:
            # Create the document metadata
            file_metadata = {
                'name': title,
                'mimeType': 'application/vnd.google-apps.document'
            }
            
            # If folder_id is specified, add it to parents
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Create the document
            file = self.service.files().create(
                body=file_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            # If content is provided, add it to the document
            if content:
                self.update_document_content(file['id'], content)
            
            # Return Pydantic model
            return GoogleDriveDocument(
                id=file['id'],
                title=file['name'],
                url=file['webViewLink']
            )
            
        except Exception as e:
            print(f"❌ Error creating document: {e}")
            return None
    
    def create_text_file(self, title, content="", folder_id=None):
        """
        Create a plain text file in Google Drive
        
        Args:
            title: The title/name of the file (should include .txt extension)
            content: Text content for the file
            folder_id: Google Drive folder ID to create the file in (optional)
        
        Returns:
            dict with 'id', 'url', and 'title' of the created file
        """
        try:
            from googleapiclient.http import MediaInMemoryUpload
            
            # Create the file metadata
            file_metadata = {
                'name': title if title.endswith('.txt') else f"{title}.txt"
            }
            
            # If folder_id is specified, add it to parents
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Create media upload with text content
            media = MediaInMemoryUpload(
                content.encode('utf-8'),
                mimetype='text/plain'
            )
            
            # Create the file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            
            return {
                'id': file['id'],
                'url': file['webViewLink'],
                'title': file['name']
            }
            
        except Exception as e:
            print(f"❌ Error creating text file: {e}")
            return None
    
    def extract_document_id_from_url(self, url):
        """
        Extract document ID from various Google Docs URL formats
        
        Args:
            url: Google Docs URL
            
        Returns:
            Document ID or None if not found
        """
        import re
        
        # Pattern to match Google Docs URLs and extract document ID
        patterns = [
            r'/document/d/([a-zA-Z0-9-_]+)',           # Standard format
            r'/document/u/\d+/d/([a-zA-Z0-9-_]+)',     # With user identifier /u/0/d/
            r'id=([a-zA-Z0-9-_]+)',                     # Query parameter format
            r'^([a-zA-Z0-9-_]+)$'                      # Just the ID itself
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def get_document_content(self, document_url_or_id):
        """
        Get the text content of a Google Doc
        
        Args:
            document_url_or_id: Google Docs URL or document ID
            
        Returns:
            dict with 'content' (text) and 'document_id'
        """
        try:
            from googleapiclient.discovery import build
            
            # Extract document ID from URL if needed
            document_id = self.extract_document_id_from_url(document_url_or_id)
            if not document_id:
                print(f"❌ Could not extract document ID from: {document_url_or_id}")
                return None
            
            # Build the Docs service
            docs_service = build('docs', 'v1', credentials=self.credentials)
            
            # Get the document
            document = docs_service.documents().get(documentId=document_id).execute()
            
            # Extract text content
            content = self._extract_text_from_document(document)
            
            return {
                'content': content,
                'document_id': document_id,
                'title': document.get('title', 'Untitled')
            }
            
        except Exception as e:
            print(f"❌ Error getting document content: {e}")
            return None
    
    def append_to_document(self, document_url_or_id, content):
        """
        Append content to the end of a Google Doc
        
        Args:
            document_url_or_id: Google Docs URL or document ID
            content: Text content to append
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from googleapiclient.discovery import build
            
            # Extract document ID from URL if needed
            document_id = self.extract_document_id_from_url(document_url_or_id)
            if not document_id:
                print(f"❌ Could not extract document ID from: {document_url_or_id}")
                return False
            
            # Build the Docs service
            docs_service = build('docs', 'v1', credentials=self.credentials)
            
            # Get document to find the end index
            document = docs_service.documents().get(documentId=document_id).execute()
            end_index = document['body']['content'][-1]['endIndex'] - 1
            
            # Append text at the end
            requests = [{
                'insertText': {
                    'location': {'index': end_index},
                    'text': content
                }
            }]
            
            docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Error appending to document: {e}")
            return False
    
    def update_document_content(self, document_id, content):
        """
        Update the content of a Google Doc (insert at beginning)
        
        Args:
            document_id: The Google Doc ID
            content: New text content to insert
        """
        try:
            from googleapiclient.discovery import build
            
            # Build the Docs service for content manipulation
            docs_service = build('docs', 'v1', credentials=self.credentials)
            
            # Insert text at the beginning of the document
            requests = [{
                'insertText': {
                    'location': {'index': 1},
                    'text': content
                }
            }]
            
            docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Error updating document content: {e}")
            return False
    
    def _extract_text_from_document(self, document):
        """
        Extract plain text from a Google Docs document structure
        
        Args:
            document: Document object from Google Docs API
            
        Returns:
            Plain text content
        """
        content = []
        
        def extract_text_from_element(element):
            if 'paragraph' in element:
                paragraph = element['paragraph']
                if 'elements' in paragraph:
                    for elem in paragraph['elements']:
                        if 'textRun' in elem:
                            content.append(elem['textRun']['content'])
            elif 'table' in element:
                # Handle tables
                table = element['table']
                for row in table.get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        for cell_element in cell.get('content', []):
                            extract_text_from_element(cell_element)
        
        # Process all content elements
        for element in document.get('body', {}).get('content', []):
            extract_text_from_element(element)
        
        return ''.join(content)
    
    def get_document_url(self, file_id):
        """
        Get the shareable URL for a Google Drive file
        
        Args:
            file_id: The Google Drive file ID
        
        Returns:
            The shareable URL or None if error
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink,webContentLink'
            ).execute()
            
            return {
                'view_url': file.get('webViewLink'),
                'download_url': file.get('webContentLink')
            }
            
        except Exception as e:
            print(f"❌ Error getting document URL: {e}")
            return None
    
    def make_document_public(self, file_id):
        """
        Make a document publicly viewable (anyone with link can view)
        
        Args:
            file_id: The Google Drive file ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            
            self.service.permissions().create(
                fileId=file_id,
                body=permission
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Error making document public: {e}")
            return False
    
    def share_document_with_email(self, file_id, email, role='reader'):
        """
        Share a document with a specific email address
        
        Args:
            file_id: The Google Drive file ID
            email: Email address to share with
            role: Permission role ('reader', 'writer', 'commenter')
        
        Returns:
            True if successful, False otherwise
        """
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Error sharing document: {e}")
            return False
    
    def list_files(self, query=None, max_results=10):
        """
        List files in Google Drive
        
        Args:
            query: Search query (optional)
            max_results: Maximum number of results
        
        Returns:
            List of files
        """
        try:
            # Build query
            search_query = query if query else "trashed=false"
            
            results = self.service.files().list(
                q=search_query,
                pageSize=max_results,
                fields="files(id,name,mimeType,webViewLink,createdTime)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return []
    
    def delete_file(self, file_id):
        """
        Delete a file from Google Drive
        
        Args:
            file_id: The Google Drive file ID
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True
            
        except Exception as e:
            print(f"❌ Error deleting file: {e}")
            return False
    
    def copy_file(self, file_id: str, new_name: str = None, destination_folder_id: str = None) -> Optional[GoogleDriveFile]:
        """
        Copy a file and optionally rename it and move it to a different folder
        
        Args:
            file_id: The Google Drive file ID to copy
            new_name: New name for the copied file (optional)
            destination_folder_id: Google Drive folder ID to copy the file to (optional)
        
        Returns:
            GoogleDriveFile object or None if error
        """
        try:
            # Get the original file metadata
            original_file = self.service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,webViewLink'
            ).execute()
            
            # Prepare the copy metadata
            copy_metadata = {
                'name': new_name if new_name else f"Copy of {original_file['name']}"
            }
            
            # If destination folder is specified, add it to parents
            if destination_folder_id:
                copy_metadata['parents'] = [destination_folder_id]
            
            # Copy the file
            copied_file = self.service.files().copy(
                fileId=file_id,
                body=copy_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            print(f"✅ Copied file: {original_file['name']} -> {copied_file['name']} (ID: {copied_file['id']})")
            
            # Return Pydantic model
            return GoogleDriveFile(
                id=copied_file['id'],
                title=copied_file['name'],
                url=copied_file['webViewLink']
            )
            
        except Exception as e:
            print(f"❌ Error copying file: {e}")
            return None
    
    def copy_document(self, document_id: str, new_name: str = None, destination_folder_id: str = None) -> Optional[GoogleDriveDocument]:
        """
        Copy a Google Doc and optionally rename it and move it to a different folder
        
        Args:
            document_id: The Google Drive document ID to copy
            new_name: New name for the copied document (optional)
            destination_folder_id: Google Drive folder ID to copy the document to (optional)
        
        Returns:
            GoogleDriveDocument object or None if error
        """
        try:
            # Get the original document metadata
            original_doc = self.service.files().get(
                fileId=document_id,
                fields='id,name,mimeType,webViewLink'
            ).execute()
            
            # Prepare the copy metadata
            copy_metadata = {
                'name': new_name if new_name else f"Copy of {original_doc['name']}"
            }
            
            # If destination folder is specified, add it to parents
            if destination_folder_id:
                copy_metadata['parents'] = [destination_folder_id]
            
            # Copy the document
            copied_doc = self.service.files().copy(
                fileId=document_id,
                body=copy_metadata,
                fields='id,name,webViewLink'
            ).execute()
            
            print(f"✅ Copied document: {original_doc['name']} -> {copied_doc['name']} (ID: {copied_doc['id']})")
            
            # Return Pydantic model
            return GoogleDriveDocument(
                id=copied_doc['id'],
                title=copied_doc['name'],
                url=copied_doc['webViewLink']
            )
            
        except Exception as e:
            print(f"❌ Error copying document: {e}")
            return None


# Convenience functions for quick access
def create_folder(folder_name: str, parent_folder_id: str = None, credentials_path: str = "credentials/client_secrets.json") -> Optional[GoogleDriveFolder]:
    """Quick function to create a Google Drive folder"""
    service = GoogleDriveService(credentials_path)
    return service.create_folder(folder_name, parent_folder_id)


def create_google_doc(title: str, content: str = "", folder_id: str = None, credentials_path: str = "credentials/client_secrets.json") -> Optional[GoogleDriveDocument]:
    """Quick function to create a Google Doc"""
    service = GoogleDriveService(credentials_path)
    return service.create_text_document(title, content, folder_id)


def create_text_file(title: str, content: str = "", folder_id: str = None, credentials_path: str = "credentials/client_secrets.json") -> Optional[GoogleDriveFile]:
    """Quick function to create a text file"""
    service = GoogleDriveService(credentials_path)
    return service.create_text_file(title, content, folder_id)


def copy_file(file_id: str, new_name: str = None, destination_folder_id: str = None, credentials_path: str = "credentials/client_secrets.json") -> Optional[GoogleDriveFile]:
    """Quick function to copy a file"""
    service = GoogleDriveService(credentials_path)
    return service.copy_file(file_id, new_name, destination_folder_id)


def copy_document(document_id: str, new_name: str = None, destination_folder_id: str = None, credentials_path: str = "credentials/client_secrets.json") -> Optional[GoogleDriveDocument]:
    """Quick function to copy a Google Doc"""
    service = GoogleDriveService(credentials_path)
    return service.copy_document(document_id, new_name, destination_folder_id)


def get_file_url(file_id: str, credentials_path: str = "credentials/client_secrets.json"):
    """Quick function to get file URL"""
    service = GoogleDriveService(credentials_path)
    return service.get_document_url(file_id)


def get_document_content(document_url: str, credentials_path: str = "credentials/client_secrets.json"):
    """Quick function to get document content from URL"""
    service = GoogleDriveService(credentials_path)
    return service.get_document_content(document_url)


def append_to_document(document_url: str, content: str, credentials_path: str = "credentials/client_secrets.json"):
    """Quick function to append content to a document"""
    service = GoogleDriveService(credentials_path)
    return service.append_to_document(document_url, content)