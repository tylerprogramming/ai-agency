#!/usr/bin/env python3
"""
Google Sheets Services - Methods for updating and managing Google Sheets
"""

from .google_sheets_auth import GoogleSheetsAuth


class GoogleSheetsService:
    """Service class for Google Sheets operations"""
    
    def __init__(self, credentials_path="credentials/client_secrets.json"):
        """Initialize the service with credentials"""
        self.auth = GoogleSheetsAuth(credentials_path)
        self.service = self.auth.get_sheets_service()
    
    def update_cell_value(self, spreadsheet_id, cell_range, value):
        """
        Update a cell with a simple text value
        
        Args:
            spreadsheet_id: The spreadsheet ID
            cell_range: Cell reference like "A1" or "Sheet1!A1"
            value: The text value to insert
        """
        try:
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=cell_range,
                valueInputOption="USER_ENTERED",
                body={"values": [[value]]}
            ).execute()
            return result
        except Exception as e:
            print(f"❌ Error updating cell {cell_range}: {e}")
            return None
    
    def update_cell_with_hyperlink(self, spreadsheet_id, sheet_id, row, col, text, url, 
                                 highlight_color=None, text_format=None):
        """
        Update a cell with text and hyperlink with full formatting control
        
        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_id: The sheet ID (0 for first sheet)
            row: Row index (0-based)
            col: Column index (0-based)
            text: Display text for the hyperlink
            url: The URL to link to
            highlight_color: Color dict, color name string ('green', 'blue', etc.), or None
            text_format: Format dict, format name string ('bold_blue', 'no_underline', etc.), or None
        """
        try:
            # Handle color names or use default
            if highlight_color is None:
                highlight_color = {"red": 1.0, "green": 1.0, "blue": 0.8}  # Light yellow
            elif isinstance(highlight_color, str):
                # Convert color name to color object
                colors = self.get_highlight_colors()
                highlight_color = colors.get(highlight_color, colors['yellow'])
            
            # Handle text format names or use default
            if text_format is None:
                text_format = {
                    "underline": True,
                    "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 1.0},  # Blue color
                    "bold": False
                }
            elif isinstance(text_format, str):
                # Convert text format name to format object
                formats = self.get_text_formats()
                text_format = formats.get(text_format, formats['default'])
            
            # Build the cell format with hyperlink and text styling
            cell_format = {
                "textFormat": {
                    "link": {"uri": url},
                    **text_format  # Merge text formatting options
                },
                "backgroundColor": highlight_color
            }
            
            result = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={
                    "requests": [{
                        "repeatCell": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": row,
                                "endRowIndex": row + 1,
                                "startColumnIndex": col,
                                "endColumnIndex": col + 1
                            },
                            "cell": {
                                "userEnteredValue": {"stringValue": text},
                                "userEnteredFormat": cell_format
                            },
                            "fields": "userEnteredValue,userEnteredFormat"
                        }
                    }]
                }
            ).execute()
            return result
        except Exception as e:
            print(f"❌ Error updating cell ({row}, {col}) with hyperlink: {e}")
            return None
    
    def update_cell_with_hyperlink_by_ref(self, spreadsheet_id, sheet_name, cell_ref, text, url, 
                                        highlight_color=None, text_format=None):
        """
        Update a cell with text and hyperlink using cell reference, with full formatting
        
        Args:
            spreadsheet_id: The spreadsheet ID
            sheet_name: Name of the sheet
            cell_ref: Cell reference like "A1", "B5", etc.
            text: Display text for the hyperlink
            url: The URL to link to
            highlight_color: Color dict, color name string ('green', 'blue', etc.), or None
            text_format: Format dict, format name string ('bold_blue', 'no_underline', etc.), or None
        """
        # Convert cell reference to row/col indices
        row, col = self._cell_ref_to_indices(cell_ref)
        
        # Get sheet ID by name
        sheet_id = self._get_sheet_id_by_name(spreadsheet_id, sheet_name)
        if sheet_id is None:
            print(f"❌ Sheet '{sheet_name}' not found")
            return None
        
        return self.update_cell_with_hyperlink(spreadsheet_id, sheet_id, row, col, text, url, 
                                             highlight_color, text_format)
    
    @staticmethod
    def get_highlight_colors():
        """Get predefined highlight colors for easy use"""
        return {
            'yellow': {"red": 1.0, "green": 1.0, "blue": 0.8},      # Light yellow (default)
            'green': {"red": 0.8, "green": 1.0, "blue": 0.8},       # Light green
            'blue': {"red": 0.8, "green": 0.9, "blue": 1.0},        # Light blue
            'red': {"red": 1.0, "green": 0.8, "blue": 0.8},         # Light red
            'orange': {"red": 1.0, "green": 0.9, "blue": 0.8},      # Light orange
            'purple': {"red": 0.9, "green": 0.8, "blue": 1.0},      # Light purple
            'none': None  # No highlighting
        }
    
    @staticmethod
    def get_text_formats():
        """Get predefined text formatting options for hyperlinks"""
        return {
            'default': {
                "underline": True,
                "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 1.0},  # Blue
                "bold": False
            },
            'bold_blue': {
                "underline": True,
                "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 1.0},  # Blue
                "bold": True
            },
            'no_underline': {
                "underline": False,
                "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 1.0},  # Blue
                "bold": False
            },
            'red_bold': {
                "underline": True,
                "foregroundColor": {"red": 1.0, "green": 0.0, "blue": 0.0},  # Red
                "bold": True
            },
            'green_no_underline': {
                "underline": False,
                "foregroundColor": {"red": 0.0, "green": 0.8, "blue": 0.0},  # Green
                "bold": False
            },
            'black_plain': {
                "underline": False,
                "foregroundColor": {"red": 0.0, "green": 0.0, "blue": 0.0},  # Black
                "bold": False
            }
        }
    
    def batch_update_cells(self, spreadsheet_id, updates):
        """
        Update multiple cells in a single batch request
        
        Args:
            spreadsheet_id: The spreadsheet ID
            updates: List of update dictionaries with keys:
                    - 'range': Cell range like "A1"
                    - 'value': Text value
                    - 'hyperlink': Optional URL for hyperlink
        """
        requests = []
        
        for update in updates:
            cell_range = update['range']
            value = update['value']
            hyperlink = update.get('hyperlink')
            
            if hyperlink:
                # Parse range to get sheet and cell info
                # This is a simplified version - you might want to enhance this
                row, col = self._cell_ref_to_indices(cell_range.split('!')[-1])
                sheet_id = 0  # Default to first sheet
                
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row,
                            "endRowIndex": row + 1,
                            "startColumnIndex": col,
                            "endColumnIndex": col + 1
                        },
                        "cell": {
                            "userEnteredValue": {"stringValue": value},
                            "userEnteredFormat": {
                                "textFormat": {"link": {"uri": hyperlink}}
                            }
                        },
                        "fields": "userEnteredValue,userEnteredFormat.textFormat.link"
                    }
                })
            else:
                # Simple value update
                requests.append({
                    "updateCells": {
                        "range": self._range_to_grid_range(cell_range),
                        "rows": [{
                            "values": [{
                                "userEnteredValue": {"stringValue": value}
                            }]
                        }],
                        "fields": "userEnteredValue"
                    }
                })
        
        try:
            result = self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body={"requests": requests}
            ).execute()
            return result
        except Exception as e:
            print(f"❌ Error in batch update: {e}")
            return None
    
    def _cell_ref_to_indices(self, cell_ref):
        """Convert cell reference like 'A1' to (row, col) indices (0-based)"""
        col_str = ""
        row_str = ""
        
        for char in cell_ref:
            if char.isalpha():
                col_str += char
            else:
                row_str += char
        
        # Convert column letters to number (A=0, B=1, etc.)
        col = 0
        for char in col_str:
            col = col * 26 + (ord(char.upper()) - ord('A') + 1)
        col -= 1  # Convert to 0-based
        
        # Convert row to 0-based
        row = int(row_str) - 1
        
        return row, col
    
    def _get_sheet_id_by_name(self, spreadsheet_id, sheet_name):
        """Get sheet ID by sheet name"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == sheet_name:
                    return sheet['properties']['sheetId']
            
            return None
        except Exception as e:
            print(f"❌ Error getting sheet ID: {e}")
            return None
    
    def _range_to_grid_range(self, range_str):
        """Convert range string to GridRange format (simplified)"""
        # This is a basic implementation
        if '!' in range_str:
            sheet_name, cell_ref = range_str.split('!')
        else:
            cell_ref = range_str
        
        row, col = self._cell_ref_to_indices(cell_ref)
        
        return {
            "startRowIndex": row,
            "endRowIndex": row + 1,
            "startColumnIndex": col,
            "endColumnIndex": col + 1
        }
    
    def find_cell_by_date_and_get_cell_below(self, today_date, all_cells, rows_down=4):
        """
        Find a cell containing today's date and return the cell X rows down in the same column
        
        Args:
            today_date: String date like "6" (for 6th day)
            all_cells: List of cell dictionaries from get_all_cell_values()
            rows_down: Number of rows down to get (default 4)
        
        Returns:
            dict with cell info or None if not found
        """
        import re
        
        # Find the cell with today's date
        date_cell = None
        for cell in all_cells:
            print(cell['value'])
            if str(cell['value']).strip() == str(today_date).strip():
                date_cell = cell
                break
        
        if not date_cell:
            return None
        else:
            print("date_cell")
            print(date_cell)
        
        # Parse the cell reference (e.g., "A5" -> column A, row 5)
        cell_ref = date_cell['cell_ref']
        match = re.match(r'([A-Z]+)(\d+)', cell_ref)
        if not match:
            return None
        
        column = match.group(1)
        row = int(match.group(2))
        
        # Calculate target cell (same column, X rows down)
        target_row = row + rows_down
        target_cell_ref = f"{column}{target_row}"
        
        print("target_cell_ref")
        print(target_cell_ref)
        
        # Find the target cell in all_cells
        for cell in all_cells:
            if cell['cell_ref'] == target_cell_ref:
                # Cell exists with data - return full cell info
                return cell
        
        # Cell doesn't exist or is empty - return minimal info with target reference
        return {
            'cell_ref': target_cell_ref,
            'value': '',
            'hyperlink': None,
            'exists': False
        }

def update_cell(spreadsheet_id, cell_range, value, credentials_path="credentials/client_secrets.json"):
    """Quick function to update a single cell"""
    service = GoogleSheetsService(credentials_path)
    return service.update_cell_value(spreadsheet_id, cell_range, value)

def update_cell_with_link(spreadsheet_id, sheet_name, cell_ref, text, url, 
                         highlight_color=None, text_format=None, credentials_path="credentials/client_secrets.json"):
    """
    Quick function to update a cell with hyperlink, highlighting, and text formatting
    
    Args:
        highlight_color: Color name string ('green', 'blue', etc.) or color dict, or None
        text_format: Format name string ('bold_blue', 'no_underline', etc.) or format dict, or None
    """
    service = GoogleSheetsService(credentials_path)
    return service.update_cell_with_hyperlink_by_ref(spreadsheet_id, sheet_name, cell_ref, text, url, 
                                                    highlight_color, text_format)

def find_cell_by_date_and_get_cell_below(today_date, all_cells, rows_down=4):
    """
    Find a cell containing today's date and return the cell X rows down in the same column
    
    Args:
        today_date: String date like "6" (for 6th day)
        all_cells: List of cell dictionaries from get_all_cell_values()
        rows_down: Number of rows down to get (default 4)
    
    Returns:
        dict with cell info or None if not found
    """
    import re
    
    # Find the cell with today's date
    date_cell = None
    for cell in all_cells:
        if str(cell['value']).strip() == str(today_date).strip():
            date_cell = cell
            break
    
    if not date_cell:
        return None
    
    # Parse the cell reference (e.g., "A5" -> column A, row 5)
    cell_ref = date_cell['cell_ref']
    match = re.match(r'([A-Z]+)(\d+)', cell_ref)
    if not match:
        return None
    
    column = match.group(1)
    row = int(match.group(2))
    
    # Calculate target cell (same column, X rows down)
    target_row = row + rows_down
    target_cell_ref = f"{column}{target_row}"
    
    # Find the target cell in all_cells
    for cell in all_cells:
        if cell['cell_ref'] == target_cell_ref:
            return cell
    
    return None