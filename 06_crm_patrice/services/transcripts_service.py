#!/usr/bin/env python3
"""
TranscriptsService - fetch client transcripts from Google Sheets
"""

from typing import Optional, List, Dict, Any
from google_services.google_sheets_auth import GoogleSheetsAPI
from config import Config
from google_services.google_sheets_services import GoogleSheetsService


class TranscriptsService:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.api = GoogleSheetsAPI()

    def get_transcript(self, client_name: str) -> Optional[str]:
        spreadsheet_id = self.config.TRANSCRIPTS_SPREADSHEET_ID
        if not spreadsheet_id:
            print("❌ TRANSCRIPTS_SPREADSHEET_ID is not set")
            return None

        try:
            spreadsheet = self.api.get_spreadsheet_data(spreadsheet_id, self.config.TRANSCRIPTS_SHEET_NAME)
            target_name = (client_name or "").strip().lower()
            if not target_name:
                return None

            for sheet in spreadsheet.sheets:
                if sheet.row_count == 0:
                    continue

                # Header map from first row
                header_row = sheet.get_row(0)
                header_map = {}
                for idx, cell in enumerate(header_row):
                    header_text = (cell.formatted_value or "").strip().lower()
                    if header_text:
                        header_map[header_text] = idx

                # Explicit mapping to avoid index 0 falsiness
                name_col_idx = None
                for key in ("client", "client name", "name"):
                    if key in header_map:
                        name_col_idx = header_map[key]
                        break

                transcript_col_idx = None
                for key in ("transcription", "transcript", "transcription_summary"):
                    if key in header_map:
                        transcript_col_idx = header_map[key]
                        break

                if name_col_idx is None or transcript_col_idx is None:
                    continue

                # Iterate rows beneath header
                for r in range(1, sheet.row_count):
                    row_cells = sheet.get_row(r)
                    if name_col_idx >= len(row_cells) or transcript_col_idx >= len(row_cells):
                        continue
                    name_val = (row_cells[name_col_idx].formatted_value or "").strip().lower()
                    if not name_val:
                        continue
                    if name_val == target_name:
                        return (row_cells[transcript_col_idx].formatted_value or "").strip()

            return None
        except Exception as e:
            print(f"❌ Error reading transcripts spreadsheet: {e}")
            return None

    def list_unprocessed_clients(self) -> List[Dict[str, Any]]:
        """Return rows from the transcript sheet that are not highlighted (treated as new clients).

        A row is considered processed if any cell in that row has a non-white background color.
        """
        spreadsheet_id = self.config.TRANSCRIPTS_SPREADSHEET_ID
        sheet_name = self.config.TRANSCRIPTS_SHEET_NAME
        if not spreadsheet_id:
            print("❌ TRANSCRIPTS_SPREADSHEET_ID is not set")
            return []

        svc = self.api.service
        # Fetch only target sheet with grid data and formats
        resp = svc.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            ranges=[sheet_name],
            includeGridData=True,
            fields="sheets(properties(sheetId,title),data/rowData/values(formattedValue,effectiveFormat/backgroundColor))",
        ).execute()

        sheets = resp.get("sheets", [])
        if not sheets:
            return []

        sheet = sheets[0]
        sheet_id = sheet["properties"]["sheetId"]
        title = sheet["properties"]["title"]
        rows = sheet.get("data", [{}])[0].get("rowData", [])
        if not rows:
            return []

        # Header parsing from first row
        header_cells = rows[0].get("values", [])
        header_map: Dict[str, int] = {}
        for idx, cell in enumerate(header_cells):
            text = (cell.get("formattedValue") or "").strip().lower()
            if text:
                header_map[text] = idx

        def get_idx(*names: str) -> Optional[int]:
            for n in names:
                if n in header_map:
                    return header_map[n]
            return None

        idx_name = get_idx("client", "client name", "name")
        idx_email = get_idx("email")
        idx_phone = get_idx("phone_number", "phone number", "phone")
        idx_transcription = get_idx("transcription", "transcript")

        if idx_name is None:
            # Minimal schema requirement
            return []

        unprocessed: List[Dict[str, Any]] = []
        for r_idx in range(1, len(rows)):
            row = rows[r_idx]
            values = row.get("values", [])

            # Determine if processed by background color
            processed = False
            for c in values:
                eff = c.get("effectiveFormat", {})
                bg = eff.get("backgroundColor")
                if not bg:
                    continue
                # Treat non-white as processed
                r = bg.get("red", 1)
                g = bg.get("green", 1)
                b = bg.get("blue", 1)
                if abs(r - 1.0) > 0.01 or abs(g - 1.0) > 0.01 or abs(b - 1.0) > 0.01:
                    processed = True
                    break

            if processed:
                continue

            def get_val(idx: Optional[int]) -> str:
                if idx is None or idx >= len(values):
                    return ""
                return (values[idx].get("formattedValue") or "").strip()

            client_name = get_val(idx_name)
            if not client_name:
                continue
            item = {
                "sheet_id": sheet_id,
                "sheet_title": title,
                "row_index": r_idx,  # 0-based
                "name": client_name,
                "email": get_val(idx_email),
                "phone": get_val(idx_phone),
                "transcription": get_val(idx_transcription),
                "num_columns": len(header_cells) if header_cells else len(values),
            }
            unprocessed.append(item)

        return unprocessed

    def mark_row_processed(self, sheet_id: int, row_index_zero_based: int, num_columns: int, color_name: str = "green") -> None:
        """Highlight a row to mark as processed using a light background color."""
        colors = GoogleSheetsService.get_highlight_colors()
        color = colors.get(color_name, colors["yellow"])
        spreadsheet_id = self.config.TRANSCRIPTS_SPREADSHEET_ID
        if not spreadsheet_id:
            return
        body = {
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": row_index_zero_based,
                            "endRowIndex": row_index_zero_based + 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": max(1, num_columns),
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": color,
                            }
                        },
                        "fields": "userEnteredFormat.backgroundColor",
                    }
                }
            ]
        }
        self.api.service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()


