from datetime import datetime, timedelta
import re


def resolve_date_light(date_phrase: str, current_date: datetime) -> str:
    today = current_date.date()
    txt = date_phrase.lower().strip()

    # ISO
    iso = re.search(r"(\d{4}-\d{2}-\d{2})", txt)
    if iso:
        return iso.group(1)

    if "tomorrow" in txt:
        return (today + timedelta(days=1)).isoformat()

    if "day after tomorrow" in txt:
        return (today + timedelta(days=2)).isoformat()

    if "today" in txt:
        return today.isoformat()

    # in N days/weeks
    m_days = re.search(r"in\s+(\d+)\s*day", txt)
    if m_days:
        return (today + timedelta(days=int(m_days.group(1)))).isoformat()

    m_weeks = re.search(r"in\s+(\d+)\s*week", txt)
    if m_weeks:
        return (today + timedelta(weeks=int(m_weeks.group(1)))).isoformat()

    # weekdays
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
    }

    for name, idx in weekdays.items():
        if name in txt:
            diff = idx - today.weekday()
            if diff <= 0:
                diff += 7
            if "next" in txt:
                diff += 7
            return (today + timedelta(days=diff)).isoformat()

    return "ERROR_FORMAT"