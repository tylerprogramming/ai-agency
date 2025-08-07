import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
from typing import Optional
from models.sheet_model import Spreadsheet

class GoogleSheetsAuth:
    def __init__(self, credentials_file: str = "credentials/client_secrets.json", token_file: str = "credentials/token.json"):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/documents'
        ]
        
    def get_credentials(self, scopes: list = None) -> Optional[Credentials]:
        """Get valid credentials, handling the full OAuth flow if needed"""
        # Use provided scopes or fall back to default
        auth_scopes = scopes if scopes else self.scopes
        creds = None
        
        # Load existing credentials if they exist
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, auth_scopes)
        
        # If there are no valid credentials, go through the OAuth flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Refresh expired credentials
                print("🔄 Refreshing expired credentials...")
                creds.refresh(GoogleRequest())
            else:
                # Run OAuth flow for new credentials
                print("🔐 Starting OAuth flow...")
                flow = Flow.from_client_secrets_file(
                    self.credentials_file, 
                    scopes=auth_scopes
                )
                flow.redirect_uri = 'http://localhost:8080/callback'
                
                auth_url, _ = flow.authorization_url(prompt='consent')
                print(f"🌐 Please visit this URL to authorize the application:")
                print(f"   {auth_url}")
                
                # Get the authorization code from user
                auth_code = input("\n📝 Enter the authorization code: ").strip()
                
                try:
                    flow.fetch_token(code=auth_code)
                    creds = flow.credentials
                    print("✅ Authorization successful!")
                except Exception as e:
                    print(f"❌ Authorization failed: {e}")
                    return None
            
            # Save the credentials for the next run
            os.makedirs(os.path.dirname(self.token_file), exist_ok=True)
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
            print(f"💾 Credentials saved to {self.token_file}")
        
        return creds
    
    def get_sheets_service(self):
        """Get authenticated Google Sheets service"""
        creds = self.get_credentials()
        if not creds:
            raise Exception("Could not get valid credentials")
        
        return build('sheets', 'v4', credentials=creds)

class GoogleSheetsAPI:
    def __init__(self, auth: GoogleSheetsAuth = None):
        self.auth = auth or GoogleSheetsAuth()
        self._service = None
    
    @property
    def service(self):
        """Lazy loading of the Google Sheets service"""
        if self._service is None:
            self._service = self.auth.get_sheets_service()
        return self._service
    
    def get_spreadsheet_data(self, spreadsheet_id: str, sheet_name: str = None, range_name: str = None) -> Spreadsheet:
        """
        Get spreadsheet data using Google Sheets API
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            sheet_name: Name of the sheet (optional)
            range_name: Range like 'A1:Z100' (optional)
        
        Returns:
            Spreadsheet object with clean Cell/Sheet models
        """
        try:
            # Get spreadsheet metadata
            spreadsheet = self.service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            
            result = {
                'title': spreadsheet['properties']['title'],
                'spreadsheet_id': spreadsheet_id,
                'spreadsheet_url': f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit',
                'sheets': []
            }
            
            # Process each sheet
            for sheet_props in spreadsheet['sheets']:
                sheet_title = sheet_props['properties']['title']
                sheet_id = sheet_props['properties']['sheetId']
                
                # Skip if specific sheet requested and this isn't it
                if sheet_name and sheet_title != sheet_name:
                    continue
                
                # Determine range to fetch
                if range_name:
                    fetch_range = f"{sheet_title}!{range_name}"
                else:
                    fetch_range = sheet_title  # Get all data
                
                # Get values using the simple API
                values_response = self.service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=fetch_range,
                    valueRenderOption='FORMATTED_VALUE'
                ).execute()
                
                # raw_response = self.service.spreadsheets().values().get(
                #     spreadsheetId=spreadsheet_id,
                #     range=fetch_range,
                #     valueRenderOption='UNFORMATTED_VALUE'
                # ).execute()
                
                formatted_values = values_response.get('values', [])
                # raw_values = raw_response.get('values', [])
                
                # Get hyperlinks using includeGridData
                grid_response = self.service.spreadsheets().get(
                    spreadsheetId=spreadsheet_id,
                    ranges=[fetch_range],
                    includeGridData=True,
                    fields='sheets/data/rowData/values(hyperlink,formattedValue,userEnteredValue)'
                ).execute()
                
                # Extract hyperlinks from grid data
                hyperlinks = self._extract_hyperlinks_from_grid_data(grid_response, sheet_title)
                
                # Store the sheet data
                sheet_data = {
                    'title': sheet_title,
                    'sheet_id': sheet_id,
                    'range': values_response.get('range', fetch_range),
                    'formatted_values': formatted_values,
                    'hyperlinks': hyperlinks,
                    'row_count': len(formatted_values),
                    'max_column_count': max(len(row) for row in formatted_values) if formatted_values else 0
                }
                
                result['sheets'].append(sheet_data)
            
            # Convert to Spreadsheet model and return
            return Spreadsheet(result)
            
        except Exception as e:
            raise Exception(f"Error fetching spreadsheet data: {e}")
    
    def _extract_hyperlinks_from_grid_data(self, grid_response, sheet_title):
        """Extract hyperlinks from grid data response"""
        hyperlinks = {}
        
        if 'sheets' not in grid_response:
            return hyperlinks
        
        for sheet in grid_response['sheets']:
            if 'data' not in sheet:
                continue
                
            for data_range in sheet['data']:
                if 'rowData' not in data_range:
                    continue
                
                for row_idx, row_data in enumerate(data_range['rowData']):
                    if 'values' not in row_data:
                        continue
                        
                    for col_idx, cell_data in enumerate(row_data['values']):
                        if 'hyperlink' in cell_data:
                            # Convert to 1-based row/col for easier reference
                            row_num = row_idx + 1
                            col_num = col_idx + 1
                            col_letter = self._number_to_column_letter(col_num)
                            
                            cell_ref = f"{col_letter}{row_num}"
                            hyperlinks[cell_ref] = {
                                'row': row_num,
                                'col': col_num,
                                'col_letter': col_letter,
                                'hyperlink': cell_data['hyperlink'],
                                'formatted_value': cell_data.get('formattedValue', ''),
                                'user_entered_value': cell_data.get('userEnteredValue', '')
                            }
        
        return hyperlinks
    
    def _number_to_column_letter(self, n):
        """Convert column number to letter (1 = A, 26 = Z, 27 = AA)"""
        result = ""
        while n > 0:
            n -= 1
            result = chr(65 + (n % 26)) + result
            n //= 26
        return result
    
# Convenience function
def get_google_sheets_data(spreadsheet_id: str, sheet_name: str = None, range_name: str = None) -> Spreadsheet:
    """
    Convenience function to get Google Sheets data using desktop app credentials
    
    Usage:
        spreadsheet = get_google_sheets_data('your_spreadsheet_id', 'July')
        july_sheet = spreadsheet.get_sheet('July')
        cell = july_sheet.get_cell(0, 0)  # A1
    """
    api = GoogleSheetsAPI()
    return api.get_spreadsheet_data(spreadsheet_id, sheet_name, range_name)