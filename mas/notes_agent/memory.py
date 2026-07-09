import json
import os
from typing import List, Optional
from datetime import datetime
from notes_agent.models import Note
import uuid
# from notes_agent.logger import logger

DB_PATH = "notes_db.json"


def _load_db():
    if not os.path.exists(DB_PATH):
        return []
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_db(data):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def add_note(task: str, date: str) -> dict:
    # logger.info("db_add_note", task=task, date=date)
    db = _load_db()

    note = Note(
        id=str(uuid.uuid4()),
        task=task,
        date=date,
        created_at=datetime.utcnow().isoformat()
    )

    db.append(note.dict())
    _save_db(db)

    return note.dict()


def get_notes(start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[dict]:
    db = _load_db()
    today = datetime.utcnow().date()

    # удаляем просроченные
    db = [n for n in db if datetime.fromisoformat(n["date"]).date() >= today]
    _save_db(db)

    results = db

    if start_date:
        results = [n for n in results if n["date"] >= start_date]

    if end_date:
        results = [n for n in results if n["date"] <= end_date]

    results.sort(key=lambda x: x["date"])

    return results


def delete_note(note_id: str) -> str:
    db = _load_db()
    new_db = [n for n in db if n["id"] != note_id]

    _save_db(new_db)

    return f"Deleted note {note_id}"