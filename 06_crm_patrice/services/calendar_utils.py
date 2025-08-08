#!/usr/bin/env python3
"""
Calendar utility functions
"""

from typing import List, Optional, Tuple, Dict, Any
from datetime import date, timedelta, datetime as _dt
from get_spreadsheet_calendar_daily_metrics import DailyMetricsReader


def get_next_weekdays(count: int, weekday_name: str = "MONDAY") -> List[date]:
    name_to_idx = {
        "MONDAY": 0,
        "TUESDAY": 1,
        "WEDNESDAY": 2,
        "THURSDAY": 3,
        "FRIDAY": 4,
        "SATURDAY": 5,
        "SUNDAY": 6,
    }
    target_idx = name_to_idx.get(weekday_name.upper(), 0)
    today = date.today()
    days_ahead = (target_idx - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    first_date = today + timedelta(days=days_ahead)
    return [first_date + timedelta(weeks=i) for i in range(count)]


def col_letter(n: int) -> str:
    result = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


def find_first_available_slot_after_day(
    reader: DailyMetricsReader,
    spreadsheet_id: str,
    sheet,
    month_name: str,
    day_start: int,
    max_cells_below: int,
    exclude_cells: Optional[set] = None,
    sheet_map: Optional[Dict[str, Any]] = None,
) -> Optional[Tuple[str, int, int]]:
    # Try current sheet days from day_start forward
    for day in range(day_start, day_start + 40):
        if day > 31:
            break
        pos = reader.find_day_cell(sheet, day)
        if not pos:
            continue
        row_idx0, col_idx0 = pos
        for offset in range(1, max_cells_below + 1):
            candidate_cell = sheet.get_cell(row_idx0 + offset, col_idx0)
            row_1b = (row_idx0 + offset) + 1
            col_1b = col_idx0 + 1
            candidate_value = candidate_cell.formatted_value if candidate_cell else ''
            if exclude_cells and (sheet.title, row_1b, col_1b) in exclude_cells:
                continue
            if not str(candidate_value).strip():
                return (sheet.title, row_1b, col_1b)

    # Move to next month
    now_year = _dt.now().year
    try:
        current_month_dt = _dt.strptime(f"{month_name} {now_year}", "%B %Y")
    except Exception:
        current_month_dt = _dt(now_year, 1, 1)
    next_month_year = current_month_dt.year + (1 if current_month_dt.month == 12 else 0)
    next_month_num = 1 if current_month_dt.month == 12 else current_month_dt.month + 1
    next_month_name = _dt(next_month_year, next_month_num, 1).strftime("%B")

    next_sheet = None
    if sheet_map is not None:
        next_sheet = sheet_map.get(next_month_name.lower())
    if next_sheet is None:
        next_sheet = reader.find_sheet_by_month(spreadsheet_id, next_month_name)
    if not next_sheet:
        return None
    pos = reader.find_day_cell(next_sheet, 1)
    if not pos:
        return None
    row_idx0, col_idx0 = pos
    for offset in range(1, max_cells_below + 1):
        candidate_cell = next_sheet.get_cell(row_idx0 + offset, col_idx0)
        row_1b = (row_idx0 + offset) + 1
        col_1b = col_idx0 + 1
        candidate_value = candidate_cell.formatted_value if candidate_cell else ''
        if exclude_cells and (next_sheet.title, row_1b, col_1b) in exclude_cells:
            continue
        if not str(candidate_value).strip():
            return (next_sheet.title, row_1b, col_1b)
    return None

