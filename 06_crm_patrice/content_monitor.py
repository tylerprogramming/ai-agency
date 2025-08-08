#!/usr/bin/env python3
"""
Content Monitor - organized utilities to fetch upcoming tasks from the calendar,
group them by person, and resolve Drive content per task type.
"""

import os
from datetime import timedelta, date
from typing import Dict, List, Any, Tuple, Iterable

from dotenv import load_dotenv
from config import Config
from services.calendar_utils import get_next_weekdays, col_letter
from get_spreadsheet_calendar_daily_metrics import DailyMetricsReader
from supabase import create_client, Client
from google_services.google_drive_services import GoogleDriveService
from google_services.google_sheets_services import GoogleSheetsService
from services.content_service import ContentService
import markdown as md

load_dotenv()


def _extract_name_and_task(text: str) -> Dict[str, str]:
    """Parse a cell value in the format "name: task"; fallback keeps entire text as task."""
    if not text:
        return {"name": "", "task": ""}
    parts = text.split(":", 1)
    if len(parts) == 2:
        return {"name": parts[0].strip(), "task": parts[1].strip()}
    return {"name": "", "task": text.strip()}


def _get_target_days(cfg: Config) -> List[date]:
    """Compute the first target weekday strictly after today and the subsequent span."""
    first_day = get_next_weekdays(1, cfg.CONTENT_START_WEEKDAY)[0]
    return [first_day + timedelta(days=i) for i in range(max(1, cfg.CONTENT_DAYS_SPAN))]


def _fetch_tasks_for_day(reader: DailyMetricsReader, spreadsheet_id: str, d: date) -> List[Dict[str, str]]:
    """Fetch up to 5 task cells below the day in the month sheet and parse name/task.
    Returns items with name, task, sheet_name, row (1-based), col (1-based), and original_text.
    """
    month_name = d.strftime("%B")
    month_sheet = reader.find_sheet_by_month(spreadsheet_id, month_name)
    if not month_sheet:
        return []

    pos = reader.find_day_cell(month_sheet, d.day)
    if not pos:
        return []

    row_idx0, col_idx0 = pos
    cells = reader.get_cells_below(month_sheet, row_idx0, col_idx0, count=5)
    items: List[Dict[str, str]] = []
    for cell in cells:
        val = (cell.get('value') or '').strip()
        if not val:
            continue
        parsed = _extract_name_and_task(val)
        if parsed['name'] or parsed['task']:
            items.append({
                'name': parsed['name'],
                'task': parsed['task'],
                'sheet_name': month_sheet.title,
                'row': cell.get('row'),
                'col': cell.get('col'),
                'original_text': val,
            })
    return items


def _group_tasks_by_person(tasks_by_day: Dict[str, List[Dict[str, str]]]) -> Dict[str, List[Dict[str, str]]]:
    """Group tasks by person name → list of entries with metadata, adding day_iso."""
    grouped: Dict[str, List[Dict[str, str]]] = {}
    for day_iso, items in tasks_by_day.items():
        for item in items:
            name = (item.get('name') or '').strip()
            task = (item.get('task') or '').strip()
            if not name or not task:
                continue
            entry = dict(item)
            entry['day'] = day_iso
            grouped.setdefault(name, []).append(entry)
    return grouped


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


def _fetch_doc_content_by_title(drive: GoogleDriveService, folder_id: str, title: str) -> str:
    """Fetch Google Doc content by exact name within folder; returns empty string if not found."""
    q = (
        f"'{folder_id}' in parents and trashed=false and name='{title}' "
        f"and mimeType='application/vnd.google-apps.document'"
    )
    files = drive.list_files(query=q, max_results=1)
    if not files:
        return ""
    file_id = files[0].get('id')
    doc = drive.get_document_content(file_id)
    return (doc or {}).get('content', '')


def get_upcoming_tasks() -> Dict[str, List[Dict[str, str]]]:
    cfg = Config()
    reader = DailyMetricsReader()

    # Compute target days
    days = _get_target_days(cfg)

    spreadsheet_id = cfg.CALENDAR_SPREADSHEET_ID
    if not spreadsheet_id:
        raise RuntimeError("CALENDAR_SPREADSHEET_ID not set")

    result: Dict[str, List[Dict[str, str]]] = {}

    for d in days:
        result[d.isoformat()] = _fetch_tasks_for_day(reader, spreadsheet_id, d)

    return result


def main():
    cfg = Config()
    content_service = ContentService()
    tasks_by_day = get_upcoming_tasks()

    grouped = _group_tasks_by_person(tasks_by_day)
    if not grouped:
        print("No tasks found.")
        return

    # Resolve clients and fetch content by type
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    supabase: Client = create_client(url, key)
    drive = GoogleDriveService()

    results: Dict[str, Any] = {}
    for person, items in grouped.items():
        # Supabase lookup by name
        try:
            resp = supabase.table('clients').select('id,name,google_drive_id').eq('name', person).limit(1).execute()
            rows = resp.data or []
        except Exception as e:
            print(f"❌ Supabase lookup failed for {person}: {e}")
            rows = []
        drive_id = rows[0].get('google_drive_id') if rows else None

        requested_types = {_detect_task_type(it['task']) for it in items}
        content_by_type: Dict[str, str] = {}
        if drive_id:
            for ttype in requested_types:
                if ttype in {"Blog", "Webinar", "Instagram", "Email"}:
                    content_by_type[ttype] = _fetch_doc_content_by_title(drive, drive_id, ttype)
        else:
            print(f"⚠️ No Drive folder ID for {person}")

        results[person] = {
            'client_id': rows[0].get('id') if rows else None,
            'google_drive_id': drive_id,
            'tasks': [{
                'day': it['day'],
                'task': it['task'],
                'type': _detect_task_type(it['task']),
                'sheet_name': it.get('sheet_name'),
                'row': it.get('row'),
                'col': it.get('col'),
                'original_text': it.get('original_text'),
            } for it in items],
            'content_by_type': content_by_type,
        }

    sheets = GoogleSheetsService()
    spreadsheet_id = cfg.CALENDAR_SPREADSHEET_ID
    for person, info in results.items():
        print(f"\n== {person} ==")
        print(f"Drive ID: {info.get('google_drive_id')}")
        for entry in info['tasks']:
            print(f"- {entry['day']} [{entry['type']}]: {entry['task']}")
            
            content_output = content_service.run_content_agent(
                document_type_prompt=entry['type'],
                task=entry['task'],
                extra_context=''
            )
            
            print(f"  Content: {content_output.content}")
            print(f"  Task: {content_output.task}")

            # Create a new Google Doc for this piece of content (rich formatting via HTML)
            folder_id = info.get('google_drive_id')
            if folder_id:
                try:
                    title = f"{person} - {entry['type']} - {entry['day']}"
                    html = md.markdown(content_output.content or "", extensions=['extra'])
                    doc = drive.create_document_from_html(title=title, html=html, folder_id=folder_id)
                    if doc:
                        print(f"  ✅ Created doc: {doc.url}")
                        # Add hyperlink to the original calendar cell
                        sheet_name = entry.get('sheet_name')
                        row_1b = entry.get('row')
                        col_1b = entry.get('col')
                        if sheet_name and row_1b and col_1b:
                            cell_ref = f"{col_letter(int(col_1b))}{int(row_1b)}"
                            display_text = entry.get('original_text') or f"{person}: {entry['task']}"
                            sheets.update_cell_with_hyperlink_by_ref(
                                spreadsheet_id=spreadsheet_id,
                                sheet_name=sheet_name,
                                cell_ref=cell_ref,
                                text=display_text,
                                url=doc.url,
                                highlight_color='green',
                                text_format='no_underline'
                            )
                    else:
                        print("  ❌ Failed to create Google Doc from HTML")
                except Exception as e:
                    print(f"  ❌ Error creating document: {e}")
            else:
                print("  ⚠️ Skipped doc creation: no Drive folder ID")


if __name__ == "__main__":
    main()


