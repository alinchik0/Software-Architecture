from pydantic import BaseModel
from datetime import datetime

class Note(BaseModel):
    id: str
    task: str
    date: str  # ISO YYYY-MM-DD
    created_at: str