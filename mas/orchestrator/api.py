from fastapi import FastAPI, Response
from pydantic import BaseModel
from typing import Optional
import uuid

from orchestrator.graph import build_graph
from shared.conversation_memory import (
    create_session,
    add_message,
    format_for_llm,
    list_sessions,
    delete_session
)

app = FastAPI(title="Orchestrator")
graph = build_graph()

# class UserInput(BaseModel):
#     input: str

# @app.post("/chat")
# def chat(req: UserInput):
#     result = graph.invoke({"input": req.input})
#     return {"output": result["output"]}





class ChatRequest(BaseModel):
    input: str
    session_id: Optional[str] = None  # Клиент может передать существующий ID сессии


@app.post("/chat")
def chat(req: ChatRequest, response: Response):
    # 2. Определяем или создаём сессию
    session_id = req.session_id
    if not session_id:
        # Если сессии нет, создаём новую с заголовком из начала запроса
        session_id = create_session(title=req.input[:30] + "...")

    # Устанавливаем cookie, чтобы браузер/клиент запоминал сессию на 30 дней
    response.set_cookie(key="session_id", value=session_id, max_age=60 * 60 * 24 * 30)

    # 3. Сохраняем запрос пользователя в базу
    add_message(session_id, "user", req.input)

    # 4. Получаем контекст истории (последние 6 сообщений)
    history_context = format_for_llm(session_id, limit=6)

    # 5. Формируем входные данные для графа
    # Мы добавляем историю прямо в input. Это самый безопасный способ,
    # который не требует изменений в orchestrator/graph.py или nodes.py
    if history_context:
        graph_input = f"{history_context}\n\nCurrent request: {req.input}"
    else:
        graph_input = req.input

    # 6. Вызываем граф
    result = graph.invoke({"input": graph_input})
    output_text = str(result.get("output", "No output"))

    # 7. Сохраняем ответ агента в базу
    # (agent_name="assistant", так как граф может вернуть ответ от любого агента)
    add_message(session_id, "assistant", output_text, agent_name="assistant")

    # 8. Возвращаем результат и session_id клиенту
    return {
        "output": output_text,
        "session_id": session_id
    }


# ==========================================================
# Дополнительные эндпоинты для управления диалогами (UI)
# ==========================================================

@app.get("/sessions")
def get_sessions():
    """Возвращает список всех сохранённых диалогов."""
    return {"sessions": list_sessions()}


@app.delete("/sessions/{session_id}")
def delete_session_endpoint(session_id: str):
    """Удаляет конкретный диалог и всю его историю сообщений."""
    delete_session(session_id)
    return {"status": "deleted", "session_id": session_id}