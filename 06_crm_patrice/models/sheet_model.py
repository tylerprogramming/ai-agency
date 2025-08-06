from dataclasses import dataclass
from typing import Optional, Dict, List, Any

@dataclass
class Cell:
    """Represents a single cell with its value and optional hyperlink"""
    formatted_value: str
    raw_value: Any
    hyperlink: Optional[str] = None
    
    def __str__(self):
        return self.formatted_value
    
    def has_link(self) -> bool:
        """Check if this cell has a hyperlink"""
        return self.hyperlink is not None

class Sheet:
    """Clean model for a Google Sheet with easy cell access"""
    
    def __init__(self, sheet_data: Dict[str, Any]):
        self.title = sheet_data['title']
        self.sheet_id = sheet_data['sheet_id']
        self.range = sheet_data['range']
        self.row_count = sheet_data['row_count']
        self.max_column_count = sheet_data['max_column_count']
        
        # Build cell matrix with hyperlinks
        self.cells = self._build_cell_matrix(
            sheet_data['formatted_values'],
            sheet_data.get('raw_values', []),
            sheet_data['hyperlinks']
        )
    
    def _build_cell_matrix(self, formatted_values: List[List[str]], 
                          raw_values: List[List[Any]], 
                          hyperlinks: Dict[str, Any]) -> List[List[Cell]]:
        """Build matrix of Cell objects"""
        cells = []
        
        # Use formatted_values as primary source, raw_values as fallback
        max_rows = len(formatted_values) if formatted_values else 0
        
        for row_idx in range(max_rows):
            row_cells = []
            formatted_row = formatted_values[row_idx] if row_idx < len(formatted_values) else []
            raw_row = raw_values[row_idx] if raw_values and row_idx < len(raw_values) else []
            
            max_cols = len(formatted_row)
            
            for col_idx in range(max_cols):
                formatted_val = formatted_row[col_idx] if col_idx < len(formatted_row) else ''
                raw_val = raw_row[col_idx] if raw_row and col_idx < len(raw_row) else formatted_val
                
                # Check for hyperlink
                col_letter = self._number_to_column_letter(col_idx + 1)
                cell_ref = f"{col_letter}{row_idx + 1}"
                hyperlink = hyperlinks.get(cell_ref, {}).get('hyperlink')
                
                cell = Cell(
                    formatted_value=str(formatted_val),
                    raw_value=raw_val,
                    hyperlink=hyperlink
                )
                row_cells.append(cell)
            
            cells.append(row_cells)
        
        return cells
    
    def _number_to_column_letter(self, n):
        """Convert column number to letter (1 = A, 26 = Z, 27 = AA)"""
        result = ""
        while n > 0:
            n -= 1
            result = chr(65 + (n % 26)) + result
            n //= 26
        return result
    
    def get_cell(self, row: int, col: int) -> Optional[Cell]:
        """Get cell by row/col (0-based indexing)"""
        if 0 <= row < len(self.cells) and 0 <= col < len(self.cells[row]):
            return self.cells[row][col]
        return None
    
    def get_cell_by_ref(self, cell_ref: str) -> Optional[Cell]:
        """Get cell by reference like 'A1', 'M9', etc."""
        try:
            # Parse cell reference
            col_letter = ''.join(c for c in cell_ref if c.isalpha())
            row_num = int(''.join(c for c in cell_ref if c.isdigit()))
            
            # Convert to 0-based indices
            col_num = 0
            for c in col_letter:
                col_num = col_num * 26 + (ord(c) - ord('A') + 1)
            
            return self.get_cell(row_num - 1, col_num - 1)
        except:
            return None
    
    def get_row(self, row_index: int) -> List[Cell]:
        """Get all cells in a row (0-based indexing)"""
        if 0 <= row_index < len(self.cells):
            return self.cells[row_index]
        return []
    
    def get_column(self, col_index: int) -> List[Cell]:
        """Get all cells in a column (0-based indexing)"""
        column = []
        for row in self.cells:
            if col_index < len(row):
                column.append(row[col_index])
            else:
                column.append(Cell('', ''))
        return column
    
    def find_cells_with_value(self, search_value: str) -> List[tuple]:
        """Find all cells containing a value. Returns (row, col, cell) tuples"""
        matches = []
        search_lower = str(search_value).lower()
        
        for row_idx, row in enumerate(self.cells):
            for col_idx, cell in enumerate(row):
                if search_lower in cell.formatted_value.lower():
                    matches.append((row_idx, col_idx, cell))
        
        return matches
    
    def find_cells_with_links(self) -> List[tuple]:
        """Find all cells with hyperlinks. Returns (row, col, cell) tuples"""
        matches = []
        
        for row_idx, row in enumerate(self.cells):
            for col_idx, cell in enumerate(row):
                if cell.has_link():
                    matches.append((row_idx, col_idx, cell))
        
        return matches
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'title': self.title,
            'sheet_id': self.sheet_id,
            'range': self.range,
            'row_count': self.row_count,
            'max_column_count': self.max_column_count,
            'cells': [
                [
                    {
                        'formatted_value': cell.formatted_value,
                        'raw_value': cell.raw_value,
                        'hyperlink': cell.hyperlink
                    }
                    for cell in row
                ]
                for row in self.cells
            ]
        }

class Spreadsheet:
    """Clean model for a Google Spreadsheet"""
    
    def __init__(self, api_response: Dict[str, Any]):
        self.title = api_response['title']
        self.spreadsheet_id = api_response['spreadsheet_id']
        self.spreadsheet_url = api_response['spreadsheet_url']
        
        # Convert sheets to Sheet objects
        self.sheets = [Sheet(sheet_data) for sheet_data in api_response['sheets']]
    
    def get_sheet(self, identifier) -> Optional[Sheet]:
        """Get sheet by title (str) or index (int)"""
        if isinstance(identifier, int):
            return self.sheets[identifier] if 0 <= identifier < len(self.sheets) else None
        elif isinstance(identifier, str):
            for sheet in self.sheets:
                if sheet.title == identifier:
                    return sheet
        return None
    
    def get_sheet_titles(self) -> List[str]:
        """Get list of all sheet titles"""
        return [sheet.title for sheet in self.sheets]