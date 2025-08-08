#!/usr/bin/env python3
"""
Daily Metrics - Read data from Google Sheets for current month and day
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from google_services.google_sheets_auth import GoogleSheetsAPI
from models.sheet_model import Sheet, Cell, Spreadsheet
from database.logging_service import SupabaseLoggingService

# Load environment variables
load_dotenv()

# Constants
SPREADSHEET_ID = "1DRRKrG3cSnNYDl7iUzkmk6p52SI8s31er6m3rkFBLlQ"
MAX_COLUMNS = 40
MAX_ROWS = 40

class DailyMetricsReader:
    """Class to read daily metrics from Google Sheets"""
    
    def __init__(self):
        """Initialize the Google Sheets API"""
        self.sheets_api = GoogleSheetsAPI()
        self.logging_service = SupabaseLoggingService()
    
    def get_current_month_sheet_name(self) -> str:
        """Get the current month's sheet name (case-insensitive)"""
        current_month = datetime.now().strftime("%B")  # e.g., "January", "February"
        return current_month
    
    def find_sheet_by_month(self, spreadsheet_id: str, month_name: str) -> Sheet:
        """Find a sheet by month name (case-insensitive)"""
        try:
            # Get all sheets in the spreadsheet
            spreadsheet = self.sheets_api.get_spreadsheet_data(spreadsheet_id)
            
            # Look for the month sheet (case-insensitive)
            target_month = month_name.lower()
            for sheet in spreadsheet.sheets:
                if sheet.title.lower() == target_month:
                    print(f"✅ Found sheet: {sheet.title}")
                    return sheet
            
            # If not found, try partial matches
            for sheet in spreadsheet.sheets:
                if target_month in sheet.title.lower():
                    print(f"✅ Found partial match sheet: {sheet.title}")
                    return sheet
            
            error_msg = f"No sheet found for month: {month_name}"
            print(f"❌ {error_msg}")
            print(f"Available sheets: {[sheet.title for sheet in spreadsheet.sheets]}")
            self.logging_service.log_error(error_msg, "sheet_search", metadata={
                "spreadsheet_id": spreadsheet_id,
                "month_name": month_name,
                "available_sheets": [sheet.title for sheet in spreadsheet.sheets]
            })
            return None
            
        except Exception as e:
            error_msg = f"Error finding sheet for month {month_name}: {e}"
            print(f"❌ {error_msg}")
            self.logging_service.log_error(error_msg, "sheet_search", metadata={
                "spreadsheet_id": spreadsheet_id,
                "month_name": month_name
            })
            return None
    
    def find_day_cell(self, sheet: Sheet, day_number: int) -> tuple:
        """Find the cell containing the current day number"""
        try:
            # Search through the first 40 rows and columns
            for row_idx in range(min(MAX_ROWS, len(sheet.cells))):
                for col_idx in range(min(MAX_COLUMNS, len(sheet.cells[row_idx]))):
                    cell = sheet.get_cell(row_idx, col_idx)
                    if cell:
                        # Try to convert cell value to integer and compare
                        try:
                            cell_value = int(cell.formatted_value.strip())
                            if cell_value == day_number:
                                print(f"✅ Found day {day_number} at cell {row_idx+1},{col_idx+1}")
                                return (row_idx, col_idx)
                        except (ValueError, AttributeError):
                            # Cell doesn't contain a number, continue searching
                            continue
            
            error_msg = f"Day {day_number} not found in the first {MAX_ROWS}x{MAX_COLUMNS} cells"
            print(f"❌ {error_msg}")
            self.logging_service.log_error(error_msg, "day_cell_search", metadata={"day_number": day_number})
            return None
            
        except Exception as e:
            error_msg = f"Error finding day cell: {e}"
            print(f"❌ {error_msg}")
            self.logging_service.log_error(error_msg, "day_cell_search", metadata={"day_number": day_number})
            return None
    
    def get_cells_below(self, sheet: Sheet, row: int, col: int, count: int = 5) -> list:
        """Get the specified number of cells below the given position"""
        cells = []
        try:
            for i in range(1, count + 1):  # Start from 1 to get cells below
                cell = sheet.get_cell(row + i, col)
                if cell:
                    cells.append({
                        'row': row + i + 1,  # Convert to 1-based for display
                        'col': col + 1,
                        'value': cell.formatted_value,
                        'hyperlink': cell.hyperlink,
                        'has_link': cell.has_link()
                    })
                else:
                    # Add empty cell info
                    cells.append({
                        'row': row + i + 1,
                        'col': col + 1,
                        'value': '',
                        'hyperlink': None,
                        'has_link': False
                    })
            
            print(f"✅ Retrieved {len(cells)} cells below position ({row+1}, {col+1})")
            return cells
            
        except Exception as e:
            error_msg = f"Error getting cells below: {e}"
            print(f"❌ {error_msg}")
            self.logging_service.log_error(error_msg, "cells_retrieval", metadata={
                "start_position": (row+1, col+1),
                "cell_count": count
            })
            return []
    
    def get_daily_metrics(self) -> dict:
        """Get daily metrics for the current day"""
        try:
            print("🔍 Getting daily metrics...")
            
            # Get current month and day
            current_month = self.get_current_month_sheet_name()
            current_day = datetime.now().day
            
            print(f"📅 Current month: {current_month}, day: {current_day}")
            
            # Find the sheet for current month
            sheet = self.find_sheet_by_month(SPREADSHEET_ID, current_month)
            if not sheet:
                error_msg = f'No sheet found for month: {current_month}'
                self.logging_service.log_error(error_msg, "daily_metrics_retrieval")
                return {
                    'success': False,
                    'error': error_msg,
                    'data': None
                }
            
            # Find the cell with current day
            day_cell_pos = self.find_day_cell(sheet, current_day)
            if not day_cell_pos:
                error_msg = f'Day {current_day} not found in sheet {current_month}'
                self.logging_service.log_error(error_msg, "daily_metrics_retrieval")
                return {
                    'success': False,
                    'error': error_msg,
                    'data': None
                }
            
            # Get the 5 cells below the day cell
            cells_below = self.get_cells_below(sheet, day_cell_pos[0], day_cell_pos[1], 5)
            
            result = {
                'success': True,
                'data': {
                    'month': current_month,
                    'day': current_day,
                    'sheet_name': sheet.title,
                    'day_cell_position': (day_cell_pos[0] + 1, day_cell_pos[1] + 1),  # Convert to 1-based
                    'cells_below': cells_below
                }
            }
            
            print(f"✅ Successfully retrieved daily metrics for {current_month} {current_day}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error getting daily metrics: {e}"
            print(f"❌ {error_msg}")
            self.logging_service.log_error(error_msg, "daily_metrics_retrieval")
            return {
                'success': False,
                'error': str(e),
                'data': None
            }
    
    def print_daily_metrics(self):
        """Print daily metrics in a formatted way"""
        metrics = self.get_daily_metrics()
        
        if not metrics['success']:
            print(f"❌ Failed to get daily metrics: {metrics['error']}")
            return
        
        data = metrics['data']
        print("\n" + "="*60)
        print(f"📊 DAILY METRICS - {data['month']} {data['day']}, {datetime.now().year}")
        print("="*60)
        print(f"📋 Sheet: {data['sheet_name']}")
        print(f"📍 Day cell position: {data['day_cell_position']}")
        print()
        
        print("📝 Cells below the day:")
        print("-" * 40)
        
        for i, cell_info in enumerate(data['cells_below'], 1):
            cell_value = cell_info['value'] if cell_info['value'] else '(empty)'
            hyperlink = cell_info['hyperlink'] if cell_info['hyperlink'] else 'No link'
            
            print(f"{i}. Row {cell_info['row']}, Col {cell_info['col']}: {cell_value}")
            if cell_info['has_link']:
                print(f"   🔗 Link: {hyperlink}")
            print()
        
        print("="*60)

def main():
    """Main function to test the daily metrics reader"""
    reader = DailyMetricsReader()
    reader.print_daily_metrics()

if __name__ == "__main__":
    main() 