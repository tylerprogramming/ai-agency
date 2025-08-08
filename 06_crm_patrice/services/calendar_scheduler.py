#!/usr/bin/env python3
"""
CalendarTaskScheduler - append tasks log and place weekly tasks into calendar sheets
"""

from typing import List, Optional, Set, Tuple
from google_services.google_sheets_auth import GoogleSheetsAPI
from google_services.google_sheets_auth import get_google_sheets_data
from google_services.google_sheets_services import GoogleSheetsService
from get_spreadsheet_calendar_daily_metrics import DailyMetricsReader
from .calendar_utils import get_next_weekdays, find_first_available_slot_after_day, col_letter
from config import Config
from datetime import datetime


class CalendarTaskScheduler:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.reader = DailyMetricsReader()
        self.writer = GoogleSheetsService()
        self.api = GoogleSheetsAPI()

    def append_tasks_log(self, client_name: str, tasks: List[str]) -> None:
        spreadsheet_id = self.config.CALENDAR_SPREADSHEET_ID
        if not spreadsheet_id:
            print("❌ CALENDAR_SPREADSHEET_ID is not set")
            return

        try:
            spreadsheet_data = get_google_sheets_data(spreadsheet_id)
            target_title = None
            for s in spreadsheet_data.sheets:
                if s.title.strip().lower() == self.config.CALENDAR_TASKS_SHEET_NAME.lower():
                    target_title = s.title
                    break
            if target_title is None:
                target_title = spreadsheet_data.sheets[0].title if spreadsheet_data.sheets else "Sheet1"

            timestamp = datetime.now().isoformat()
            values = [[timestamp, client_name, task] for task in tasks]

            self.api.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=f"{target_title}!A:C",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": values}
            ).execute()

            print(f"✅ Appended {len(values)} task(s) to '{target_title}' in calendar spreadsheet")
        except Exception as e:
            print(f"❌ Error appending tasks to calendar spreadsheet: {e}")

    def schedule_tasks_on_next_mondays(self, client_name: str, tasks: List[str]) -> None:
        spreadsheet_id = self.config.CALENDAR_SPREADSHEET_ID
        if not spreadsheet_id:
            print("❌ CALENDAR_SPREADSHEET_ID is not set")
            return

        cleaned_tasks = [t.strip() for t in tasks if t and str(t).strip()]
        if not cleaned_tasks:
            print("⚠️ No non-empty tasks to schedule")
            return

        next_days = get_next_weekdays(self.config.WEEKS_TO_SCHEDULE, self.config.SCHEDULE_START_WEEKDAY)
        print(f"📅 Scheduling tasks on next {len(next_days)} {self.config.SCHEDULE_START_WEEKDAY.capitalize()}s: {[d.isoformat() for d in next_days]}")

        # Preload spreadsheet metadata once and build a month->sheet map
        sheet_map = {}
        try:
            spreadsheet = get_google_sheets_data(self.config.CALENDAR_SPREADSHEET_ID)
            for s in spreadsheet.sheets:
                sheet_map[s.title.lower()] = s
        except Exception as e:
            print(f"⚠️ Could not preload calendar spreadsheet: {e}")

        for target_date in next_days:
            month_name = target_date.strftime("%B")
            day_num = target_date.day

            sheet = sheet_map.get(month_name.lower()) or self.reader.find_sheet_by_month(spreadsheet_id, month_name)
            if not sheet:
                print(f"❌ Month sheet not found for {month_name}; skipping {target_date}")
                continue

            if self.config.SPLIT_TASKS_IN_CALENDAR:
                used: Set[Tuple[str, int, int]] = set()
                for t in cleaned_tasks:
                    placement = find_first_available_slot_after_day(
                        self.reader, spreadsheet_id, sheet, month_name,
                        day_start=day_num, max_cells_below=self.config.MAX_CELLS_BELOW, exclude_cells=used, sheet_map=sheet_map
                    )
                    if not placement:
                        print(f"❌ Could not find available slot near {target_date} for task: {t}")
                        break
                    target_sheet_title, row_1b, col_1b = placement
                    a1_ref = f"{col_letter(col_1b)}{row_1b}"
                    cell_range = f"{target_sheet_title}!{a1_ref}"
                    value_text = f"{client_name}: {t}"
                    try:
                        self.writer.update_cell_value(spreadsheet_id, cell_range, value_text)
                        print(f"✅ Wrote task to {cell_range} for week of {target_date.isoformat()}")
                        used.add((target_sheet_title, row_1b, col_1b))
                    except Exception as e:
                        print(f"❌ Error writing task to {cell_range}: {e}")
            else:
                tasks_text = " | ".join(cleaned_tasks)
                value_text = f"{client_name}: {tasks_text}"
                placement = find_first_available_slot_after_day(
                    self.reader, spreadsheet_id, sheet, month_name,
                    day_start=day_num, max_cells_below=self.config.MAX_CELLS_BELOW, sheet_map=sheet_map
                )
                if not placement:
                    print(f"❌ Could not find available slot near {target_date} to place tasks")
                    continue
                target_sheet_title, row_1b, col_1b = placement
                a1_ref = f"{col_letter(col_1b)}{row_1b}"
                cell_range = f"{target_sheet_title}!{a1_ref}"
                try:
                    self.writer.update_cell_value(spreadsheet_id, cell_range, value_text)
                    print(f"✅ Wrote tasks to {cell_range} for week of {target_date.isoformat()}")
                except Exception as e:
                    print(f"❌ Error writing tasks to {cell_range}: {e}")

