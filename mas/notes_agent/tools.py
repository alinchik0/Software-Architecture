from datetime import datetime
from notes_agent.memory import add_note as db_add_note, get_notes as db_get_notes, delete_note as db_delete_note
from notes_agent.date_utils import resolve_date_light
import logging

logger = logging.getLogger(__name__)



def resolve_date(date_phrase: str) -> str:
    logger.info("resolve_date_called", extra={"date_phrase": date_phrase})
    return resolve_date_light(date_phrase, datetime.utcnow())


def add_note(task: str, date_phrase: str):
    logger.info("add_note_tool", extra={"task_preview": task[:50], "date_phrase": date_phrase})
    date = resolve_date(date_phrase)

    if date == "ERROR_FORMAT":
        logger.warning("add_note_date_parse_failed", extra={"date_phrase": date_phrase})
        return {"error": "Could not parse date. Please provide a clearer date."}

    result = db_add_note(task, date)
    logger.debug("add_note_completed", extra={"result_type": type(result).__name__})
    return result


def get_notes(start_date: str = None, end_date: str = None):
    logger.info("get_notes_tool", extra={"start_date": start_date, "end_date": end_date})
    return db_get_notes(start_date, end_date)


def delete_note(note_id: str):
    logger.info("delete_note_tool", extra={"note_id": note_id})
    return db_delete_note(note_id)