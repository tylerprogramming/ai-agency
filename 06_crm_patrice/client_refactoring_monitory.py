#!/usr/bin/env python3
"""
Client Refactoring Monitor

Scans upcoming calendar cells for red-highlighted items (meaning: needs rework),
pulls the linked Google Doc content (via cell hyperlink), runs the content agent
with extra context to improve it, creates a revised Google Doc, and updates the
calendar cell hyperlink to point to the new doc with custom formatting.
"""

import os
from datetime import timedelta, date
from typing import Dict, List, Any, Optional

import markdown as md
from dotenv import load_dotenv
from supabase import create_client, Client

from config import Config
from services.calendar_utils import get_next_weekdays, col_letter
from get_spreadsheet_calendar_daily_metrics import DailyMetricsReader
from google_services.google_sheets_auth import GoogleSheetsAuth
from google_services.google_drive_services import GoogleDriveService
from google_services.google_sheets_services import GoogleSheetsService
from services.content_service import ContentService


load_dotenv()


def _extract_name_and_task(text: str) -> Dict[str, str]:
    if not text:
        return {"name": "", "task": ""}
    parts = text.split(":", 1)
    if len(parts) == 2:
        return {"name": parts[0].strip(), "task": parts[1].strip()}
    return {"name": "", "task": text.strip()}


def _detect_task_type(task_text: str) -> str:
    t = (task_text or '').lower()
    if "blog" in t:
        return "Blog"
    if "webinar" in t:
        return "Webinar"
    if "instagram" in t or "ig" in t:
        return "Instagram"
    if "email" in t:
        return "Email"
    return "Unknown"


def _get_target_days(cfg: Config) -> List[date]:
    """Return days from today to 7 days ahead (inclusive)."""
    today = date.today()
    end = today + timedelta(days=7)
    days: List[date] = []
    cur = today
    while cur <= end:
        days.append(cur)
        cur += timedelta(days=1)
    return days


def _get_cell_background_color(spreadsheet_id: str, sheet_name: str, cell_ref: str) -> Optional[Dict[str, float]]:
    """Return backgroundColor dict with keys red/green/blue (floats 0..1) for a single cell."""
    auth = GoogleSheetsAuth()
    service = auth.get_sheets_service()
    try:
        rng = f"{sheet_name}!{cell_ref}:{cell_ref}"
        resp = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id,
            ranges=[rng],
            includeGridData=True,
            fields='sheets/data/rowData/values(effectiveFormat/backgroundColor)'
        ).execute()
        sheets = resp.get('sheets') or []
        if not sheets:
            return None
        data = (sheets[0].get('data') or [])
        if not data:
            return None
        row_data = (data[0].get('rowData') or [])
        if not row_data:
            return None
        values = (row_data[0].get('values') or [])
        if not values:
            return None
        eff = values[0].get('effectiveFormat') or {}
        bg = eff.get('backgroundColor')
        return bg
    except Exception:
        return None


def _is_color_red(bg: Optional[Dict[str, float]]) -> bool:
    """Detect standard red roughly matching Sheets UI red (~204,0,0)."""
    if not bg:
        return False
    # API returns 0..1 floats; convert to 0..255 for clearer thresholds
    def to_255(x: Optional[float]) -> int:
        try:
            return int(round(float(x or 0.0) * 255))
        except Exception:
            return 0
    r = to_255(bg.get('red'))
    g = to_255(bg.get('green'))
    b = to_255(bg.get('blue'))
    # Treat as red if high R and very low G/B
    return (r >= 190) and (g <= 20) and (b <= 20)


def _find_red_marked_items(cfg: Config) -> List[Dict[str, Any]]:
    reader = DailyMetricsReader()
    spreadsheet_id = cfg.CALENDAR_SPREADSHEET_ID
    days = _get_target_days(cfg)
    red_items: List[Dict[str, Any]] = []

    for d in days:
        month_name = d.strftime("%B")
        sheet = reader.find_sheet_by_month(spreadsheet_id, month_name)
        if not sheet:
            continue
        pos = reader.find_day_cell(sheet, d.day)
        if not pos:
            continue
        row_idx0, col_idx0 = pos
        below = reader.get_cells_below(sheet, row_idx0, col_idx0, count=5)
        for cell in below:
            text = (cell.get('value') or '').strip()
            if not text:
                continue
            # Build A1 cell ref
            row_1b = int(cell['row'])
            col_1b = int(cell['col'])
            a1 = f"{col_letter(col_1b)}{row_1b}"
            bg = _get_cell_background_color(spreadsheet_id, sheet.title, a1)
            if not _is_color_red(bg):
                continue

            parsed = _extract_name_and_task(text)
            if not (parsed['name'] and parsed['task']):
                continue

            red_items.append({
                'day': d.isoformat(),
                'sheet_name': sheet.title,
                'row': row_1b,
                'col': col_1b,
                'cell_ref': a1,
                'original_text': text,
                'name': parsed['name'],
                'task': parsed['task'],
                'hyperlink': cell.get('hyperlink'),
                'bg': bg,
            })

    return red_items


def _redo_item_with_agent(item: Dict[str, Any], supabase: Client, drive: GoogleDriveService, sheets: GoogleSheetsService, cfg: Config):
    name = item['name']
    task_text = item['task']
    doc_type = _detect_task_type(task_text)

    # Lookup client for drive folder
    try:
        resp = supabase.table('clients').select('id,name,google_drive_id').eq('name', name).limit(1).execute()
        rows = resp.data or []
    except Exception as e:
        print(f"❌ Supabase lookup failed for {name}: {e}")
        rows = []
    drive_folder_id = rows[0].get('google_drive_id') if rows else None

    # Fetch existing doc content via hyperlink (if present)
    existing_content = ""
    if item.get('hyperlink'):
        doc = drive.get_document_content(item['hyperlink'])
        existing_content = (doc or {}).get('content', '')

    # Build improvement context
    improvement_context = (
        "This content was flagged for revision. Improve clarity, tone, and impact. "
        "Keep it aligned with the requested type and task. Original below.\n\n" + existing_content
    )

    # Generate improved content
    content_service = ContentService()
    output = content_service.run_content_agent(
        document_type_prompt=doc_type,
        task=task_text,
        extra_context=improvement_context,
        verbose=True,
    )

    # Create a revised doc and update the calendar cell with link
    if drive_folder_id:
        title = f"{name} - {doc_type} - {item['day']} - Revised"
        html = md.markdown(output.content or "", extensions=['extra'])
        new_doc = drive.create_document_from_html(title=title, html=html, folder_id=drive_folder_id)
        if new_doc:
            print(f"  ✅ Revised doc created: {new_doc.url}")
            sheets.update_cell_with_hyperlink_by_ref(
                spreadsheet_id=cfg.CALENDAR_SPREADSHEET_ID,
                sheet_name=item['sheet_name'],
                cell_ref=item['cell_ref'],
                text=item['original_text'],
                url=new_doc.url,
                highlight_color='green',
                text_format='no_underline',
            )
        else:
            print("  ❌ Failed to create revised Google Doc")
    else:
        print(f"  ⚠️ No Drive folder for {name}; skipping doc creation")


def run_refactoring_check():
    """Run one pass of the refactoring monitor."""
    cfg = Config()
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, key)

    drive = GoogleDriveService()
    sheets = GoogleSheetsService()

    red_items = _find_red_marked_items(cfg)
    if not red_items:
        print("No red-marked items found to redo.")
        return {"count": 0}

    print(f"Found {len(red_items)} red-marked items to redo.")
    for item in red_items:
        print(f"- {item['day']} {item['sheet_name']}!{item['cell_ref']} :: {item['original_text']}")
        _redo_item_with_agent(item, supabase, drive, sheets, cfg)
    return {"count": len(red_items)}


def start_scheduler():
    """Run the refactoring monitor every hour using APScheduler."""
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    scheduler = BlockingScheduler()
    scheduler.add_job(
        func=run_refactoring_check,
        trigger=IntervalTrigger(hours=1),
        id='client_refactoring_monitor',
        name='Scan red-marked calendar cells every hour',
        replace_existing=True,
    )
    print("Starting APScheduler - refactoring monitor every hour... (Ctrl+C to stop)")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("Scheduler stopped by user")
        scheduler.shutdown()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        run_refactoring_check()
    else:
        start_scheduler()


