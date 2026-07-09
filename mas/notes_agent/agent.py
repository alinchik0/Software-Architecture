# notes_agent/agent.py
import logging  # ← Стандартный модуль, ничего устанавливать не нужно
import json
import time

import requests
from notes_agent.tools import add_note, get_notes, delete_note
from shared.observability import get_tracer, get_meter

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)
meter = get_meter(__name__)

# 📊 Метрики (объявляем один раз при импорте)
request_counter = meter.create_counter("notes_agent_requests")
tool_latency = meter.create_histogram("notes_agent_tool_duration_seconds", unit="s")

OLLAMA_URL = "http://localhost:11434/api/chat"


MODEL_NAME = "qwen3.5:4b-q4_K_M"


tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "add_note",
            "description": "Add a new task",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "date_phrase": {"type": "string"}
                },
                "required": ["task", "date_phrase"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_notes",
            "description": "Get notes list",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_note",
            "description": "Delete a note",
            "parameters": {
                "type": "object",
                "properties": {
                    "note_id": {"type": "string"}
                },
                "required": ["note_id"]
            }
        }
    }
]


def run_agent(user_input: str):
    try:
        with tracer.start_as_current_span("notes_agent.run") as span:
            start_time = time.time()

            # 🏷️ Семантические атрибуты для LangFuse
            span.set_attributes({
                "gen_ai.system": "ollama",
                "gen_ai.request.model": MODEL_NAME,
                "agent.type": "notes",
                "input.preview": user_input[:100]
            })

            request_counter.add(1, attributes={"operation": "request_received"})
            logger.info("notes_agent_request", extra={"input_preview": user_input[:100]})

            system_prompt = open("notes_agent/prompts/system.md").read()

            payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "tools": tools_schema,
                "stream": False
            }

            # 🎯 Спан для внешнего LLM-вызова
            with tracer.start_as_current_span("notes_agent.llm_call") as llm_span:
                llm_span.set_attribute("gen_ai.operation.name", "chat")
                response = requests.post(OLLAMA_URL, json=payload)
                data = response.json()

                llm_span.add_event("llm_response", attributes={
                    "status_code": response.status_code,
                    "has_tool_calls": "tool_calls" in data.get("message", {})
                })

            message = data.get("message", {})
            logger.debug("notes_agent_llm_raw", extra={"message_keys": list(message.keys())})

            if "tool_calls" in message:
                tool_call = message["tool_calls"][0]
                name = tool_call["function"]["name"]
                args = tool_call["function"]["arguments"]
                if isinstance(args, str):
                    args = json.loads(args)

                logger.info("notes_agent_tool_called", extra={"tool_name": name, "tool_args": args})

                # 🎯 Замеряем время выполнения инструмента
                tool_start = time.time()
                try:
                    if name == "add_note":
                        result = add_note(**args)
                    elif name == "get_notes":
                        result = get_notes(**args)
                    elif name == "delete_note":
                        result = delete_note(**args)
                    else:
                        result = "Unknown tool"

                    tool_latency.record(time.time() - tool_start, attributes={"tool": name, "status": "success"})
                    span.set_attributes({
                        "tool.name": name,
                        "tool.status": "success"
                    })
                    return result

                except Exception as tool_e:
                    tool_latency.record(time.time() - tool_start,
                                        attributes={"tool": name, "status": "error", "error": type(tool_e).__name__})
                    span.record_exception(tool_e)
                    span.set_attribute("tool.status", "error")
                    raise

            # Если нет tool_calls — возвращаем прямой ответ
            span.set_attribute("llm.direct_response", True)
            return message.get("content", "")

    except Exception as e:
        # 📉 Фиксируем общую задержку даже при ошибке
        tool_latency.record(time.time() - start_time, attributes={"operation": "run_agent", "error": type(e).__name__})
        logger.error("notes_agent_error", extra={"error": str(e), "input_preview": user_input[:100]})
        return f"Error: {str(e)}"


def handle_request(user_input: str) -> str:
    result = run_agent(user_input)
    return str(result)