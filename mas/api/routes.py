import logging
from fastapi import APIRouter, Response
from pydantic import BaseModel
from typing import Optional
from orchestrator.graph import build_graph
from shared.observability import get_tracer
from shared.conversation_memory import (
	create_session,
	add_message,
	format_for_llm,
	list_sessions,
	delete_session,
	get_recent_messages
)

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)

router = APIRouter()
graph = build_graph()


class ChatRequest(BaseModel):
	message: str
	session_id: Optional[str] = None  # Добавили поддержку сессий


@router.post("/chat")
def chat(req: ChatRequest, response: Response):
	with tracer.start_as_current_span("api_chat") as span:
		logger.info("api_request", extra={"user_input": req.message})

		try:
			# 1. Управление сессией
			session_id = req.session_id
			if not session_id:
				session_id = create_session(title=req.message[:30] + "...")

			# Сохраняем session_id в cookie на 30 дней
			response.set_cookie(key="session_id", value=session_id, max_age=60 * 60 * 24 * 30)

			# 2. Сохраняем сообщение пользователя
			add_message(session_id, "user", req.message)

			# 3. Получаем контекст истории
			history_context = format_for_llm(session_id, limit=6)

			# 4. Формируем входные данные для графа
			if history_context:
				graph_input = f"{history_context}\n\nCurrent request: {req.message}"
			else:
				graph_input = req.message

			span.set_attribute("user_input", req.message)
			span.set_attribute("session_id", session_id)

			# 5. Вызываем граф
			result = graph.invoke({"input": graph_input})
			response_text = str(result.get("output", ""))

			# 6. Сохраняем ответ бота
			add_message(session_id, "assistant", response_text, agent_name="assistant")

			logger.info("api_response", extra={"bot_response": response_text})
			span.set_attribute("response", response_text)

			return {"response": response_text, "session_id": session_id}

		except Exception as e:
			logger.error("api_error", extra={"error_details": str(e)})
			span.record_exception(e)
			return {"response": f"Error: {str(e)}", "session_id": req.session_id}


# ==========================================================
# Эндпоинты для управления историей чатов (для Sidebar UI)
# ==========================================================

@router.get("/sessions")
def get_sessions():
	"""Возвращает список всех диалогов."""
	return {"sessions": list_sessions()}


@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: str):
	"""Возвращает сообщения конкретного диалога."""
	messages = get_recent_messages(session_id, limit=100)
	return {"messages": messages}


@router.delete("/sessions/{session_id}")
def delete_session_endpoint(session_id: str):
	"""Удаляет диалог."""
	delete_session(session_id)
	return {"status": "deleted", "session_id": session_id}