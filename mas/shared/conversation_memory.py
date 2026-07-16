"""
Управление историей диалогов (сессиями).
Хранит сообщения в локальной SQLite базе.
"""
import sqlite3
import uuid
from pathlib import Path
from contextlib import contextmanager

DATA_DIR = Path.home() / ".study_agent_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "conversations.db"


@contextmanager
def get_connection():
	conn = sqlite3.connect(str(DB_PATH))
	conn.row_factory = sqlite3.Row
	try:
		yield conn
	finally:
		conn.close()


def init_db():
	with get_connection() as conn:
		# Таблица сессий (диалогов)
		conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                title TEXT DEFAULT 'New Chat',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
		# Таблица сообщений
		conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,          -- 'user' или 'assistant'
                agent_name TEXT,             -- 'notes', 'study', 'router'
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
            )
        """)
		conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp)")
		conn.commit()


def create_session(title: str = "New Chat") -> str:
	"""Создаёт новую сессию и возвращает её ID."""
	session_id = str(uuid.uuid4())
	with get_connection() as conn:
		conn.execute("INSERT INTO sessions (id, title) VALUES (?, ?)", (session_id, title))
		conn.commit()
	return session_id


def list_sessions() -> list:
	"""Возвращает список всех сессий."""
	with get_connection() as conn:
		cursor = conn.execute("SELECT id, title, created_at FROM sessions ORDER BY created_at DESC")
		return [dict(row) for row in cursor.fetchall()]


def delete_session(session_id: str):
	"""Удаляет сессию и все её сообщения."""
	with get_connection() as conn:
		conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
		conn.commit()


def add_message(session_id: str, role: str, content: str, agent_name: str = None):
	"""Добавляет сообщение в сессию. Если сессии нет, создаёт её."""
	with get_connection() as conn:
		# Проверка на случай, если сессия была удалена или не передана
		cursor = conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,))
		if cursor.fetchone() is None:
			conn.execute("INSERT INTO sessions (id, title) VALUES (?, ?)", (session_id, "Recovered Chat"))

		msg_id = str(uuid.uuid4())
		conn.execute(
			"INSERT INTO messages (id, session_id, role, agent_name, content) VALUES (?, ?, ?, ?, ?)",
			(msg_id, session_id, role, agent_name, content)
		)
		conn.commit()


def get_recent_messages(session_id: str, limit: int = 10) -> list:
	"""Возвращает последние N сообщений сессии в хронологическом порядке."""
	with get_connection() as conn:
		cursor = conn.execute(
			"SELECT role, agent_name, content, timestamp FROM messages "
			"WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
			(session_id, limit)
		)
		messages = cursor.fetchall()
		# Разворачиваем, чтобы старые сообщения были первыми
		return [
			{"role": m["role"], "agent": m["agent_name"], "content": m["content"]}
			for m in reversed(messages)
		]


def format_for_llm(session_id: str, limit: int = 10) -> str:
	"""Форматирует историю для вставки в системный промпт LLM."""
	messages = get_recent_messages(session_id, limit)
	if not messages:
		return ""

	lines = ["\n--- Previous Conversation Context ---"]
	for m in messages:
		agent_prefix = f" [{m['agent']}]" if m['agent'] else ""
		lines.append(f"{m['role'].capitalize()}{agent_prefix}: {m['content']}")
	lines.append("--- End of Context ---\n")
	return "\n".join(lines)


# Инициализация БД при импорте модуля
init_db()