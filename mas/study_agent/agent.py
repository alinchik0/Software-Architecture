# import logging
# import json
# import time
#
# import requests
# from study_agent.tools import add_material, get_material, search_material, answer_question, delete_material
# from shared.observability import get_tracer, get_meter
# from shared.llm_client import call_llm_with_tools, HF_MODEL
#
# logger = logging.getLogger(__name__)
# tracer = get_tracer(__name__)
# meter = get_meter(__name__)
#
# request_counter = meter.create_counter("study_agent_requests_total")
# request_latency = meter.create_histogram("study_agent_request_duration_seconds", unit="s")
# tool_counter = meter.create_counter("study_agent_tool_calls_total")
#
# # OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
# #
# # MODEL_NAME = "qwen3.5:4b-q4_K_M"
#
# ALLOWED_TOOLS = {
#     "add_material": add_material,
#     "get_material": get_material,
#     "search_material": search_material,
#     "delete_material": delete_material,
#     "answer_question": answer_question,
# }
#
#
# tools_schema = [
#     {
#         "type": "function",
#         "function": {
#             "name": "add_material",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "topic": {"type": "string"},
#                     "content": {"type": "string"}
#                 },
#                 "required": ["topic", "content"]
#             }
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "get_material",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "topic": {"type": "string"}
#                 },
#                 "required": ["topic"]
#             }
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "search_material",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "query": {"type": "string"}
#                 },
#                 "required": ["query"]
#             }
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "delete_material",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "topic": {"type": "string"}
#                 },
#                 "required": ["topic"]
#             }
#         }
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "answer_question",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "query": {"type": "string"}
#                 },
#                 "required": ["query"]
#             }
#         }
#     }
# ]
#
#
# def run_agent(user_input: str):
#     start_time = time.time()
#
#     with tracer.start_as_current_span("study_agent.run") as span:
#         span.set_attributes({
#             "gen_ai.system": "huggingface",
#             "gen_ai.request.model": HF_MODEL,
#             "agent.type": "study",
#             "input.preview": user_input[:100]  # Безопасный превью для трейса
#         })
#
#         request_counter.add(1, attributes={"operation": "request_received"})
#         logger.info("study_agent_request", extra={"input_preview": user_input[:100]})
#
#         try:
#             system_prompt = open("study_agent/prompts/system.md").read()
#             # payload = {
#             #     "model": MODEL_NAME,
#             #     "messages": [
#             #         {"role": "system", "content": system_prompt},
#             #         {"role": "user", "content": user_input}
#             #     ],
#             #     "tools": tools_schema,
#             #     "stream": False
#             # }
#             #
#             # # 🎯 Спан только для внешнего LLM-вызова
#             # with tracer.start_as_current_span("study_agent.llm_call") as llm_span:
#             #     llm_span.set_attribute("gen_ai.operation.name", "chat")
#             #     response = requests.post(OLLAMA_URL, json=payload)
#             #     data = response.json()
#             #
#             #     llm_span.add_event("llm_response", attributes={
#             #         "status_code": response.status_code,
#             #         "has_tool_calls": "tool_calls" in data.get("message", {})
#             #     })
#             #
#             # message = data.get("message", {})
#
#             system_prompt = open("study_agent/prompts/system.md").read()
#
#             # 🎯 Спан только для внешнего LLM-вызова
#             with tracer.start_as_current_span("study_agent.llm_call") as llm_span:
#                 llm_span.set_attribute("gen_ai.operation.name", "chat")
#                 data = call_llm_with_tools(
#                     system_prompt=system_prompt,
#                     user_prompt=user_input,
#                     tools=tools_schema,
#                     temperature=0.1,
#                     timeout=90
#                 )
#
#                 has_tool_calls = (
#                     "choices" in data
#                     and data["choices"][0].get("message", {}).get("tool_calls") is not None
#                 )
#                 llm_span.add_event("llm_response", attributes={
#                     "status_code": 200 if "error" not in data else 500,
#                     "has_tool_calls": has_tool_calls
#                 })
#
#             if "error" in data:
#                 raise Exception(data["error"])
#
#             message = data["choices"][0]["message"]
#
#
#             if "tool_calls" in message:
#                 tool_call = message["tool_calls"][0]
#                 name = tool_call["function"]["name"]
#                 args = tool_call["function"]["arguments"]
#                 if isinstance(args, str):
#                     args = json.loads(args)
#
#                 logger.info("study_agent_tool_called", extra={"tool_name": name})
#                 tool_counter.add(1, attributes={"tool": name, "status": "started"})
#
#                 # Выполнение инструмента
#                 tool_start = time.time()
#                 try:
#                     if name not in ALLOWED_TOOLS:
#                         raise ValueError(f"Unknown tool: {name}")
#
#                     result = ALLOWED_TOOLS[name](**args)
#
#                     tool_counter.add(1, attributes={"tool": name, "status": "success"})
#                     span.set_attributes({
#                         "tool.name": name,
#                         "tool.status": "success",
#                         "output.preview": str(result)[:100] if result else ""
#                     })
#                     return result
#
#                 except Exception as tool_e:
#                     tool_counter.add(1, attributes={"tool": name, "status": "error", "error": type(tool_e).__name__})
#                     span.record_exception(tool_e)
#                     span.set_attribute("tool.status", "error")
#                     raise
#
#             # Прямой ответ от LLM (без tool_call)
#             span.set_attribute("llm.direct_response", True)
#             return message.get("content", "")
#
#         except Exception as e:
#             request_counter.add(1, attributes={"operation": "request_failed", "error": type(e).__name__})
#             span.record_exception(e)
#             span.set_status({"status_code": "ERROR", "description": str(e)})
#             logger.error("study_agent_error", extra={"error": str(e), "input_preview": user_input[:100]})
#             return f"Error: {str(e)}"
#
#         finally:
#             # Фиксируем общую задержку в любом случае
#             request_latency.record(time.time() - start_time, attributes={"agent": "study"})
#
#
# def handle_request(user_input: str) -> str:
#     result = run_agent(user_input)
#     return str(result)


import logging
import json
import time

from study_agent.tools import add_material, get_material, search_material, answer_question, delete_material
from shared.observability import get_tracer, get_meter
from shared.llm_client import call_llm_json, HF_MODEL

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)
meter = get_meter(__name__)

request_counter = meter.create_counter("study_agent_requests_total")
request_latency = meter.create_histogram("study_agent_request_duration_seconds", unit="s")
tool_counter = meter.create_counter("study_agent_tool_calls_total")

ALLOWED_TOOLS = {
    "add_material": add_material,
    "get_material": get_material,
    "search_material": search_material,
    "delete_material": delete_material,
    "answer_question": answer_question,
}


def run_agent(user_input: str):
    start_time = time.time()

    with tracer.start_as_current_span("study_agent.run") as span:
        span.set_attributes({
            "gen_ai.system": "huggingface",
            "gen_ai.request.model": HF_MODEL,
            "agent.type": "study",
            "input.preview": user_input[:100]
        })

        request_counter.add(1, attributes={"operation": "request_received"})
        logger.info("study_agent_request", extra={"input_preview": user_input[:100]})

        try:
            system_prompt = open("study_agent/prompts/system.md").read()


            with tracer.start_as_current_span("study_agent.llm_call") as llm_span:
                llm_span.set_attribute("gen_ai.operation.name", "chat")

                data = call_llm_json(
                    system_prompt=system_prompt,
                    user_prompt=user_input,
                    timeout=90
                )

                llm_span.add_event("llm_response", attributes={
                    "status_code": 200 if "error" not in data else 500,
                    "has_tool": data.get("tool") is not None
                })

            if "error" in data:
                raise Exception(data["error"])

            tool_name = data.get("tool")

            if tool_name:
                args = data.get("args", {})
                logger.info("study_agent_tool_called", extra={"tool_name": tool_name})
                tool_counter.add(1, attributes={"tool": tool_name, "status": "started"})

                tool_start = time.time()
                try:
                    if tool_name not in ALLOWED_TOOLS:
                        raise ValueError(f"Unknown tool: {tool_name}")

                    result = ALLOWED_TOOLS[tool_name](**args)

                    tool_counter.add(1, attributes={"tool": tool_name, "status": "success"})
                    span.set_attributes({
                        "tool.name": tool_name,
                        "tool.status": "success",
                        "output.preview": str(result)[:100] if result else ""
                    })
                    return str(result)

                except Exception as tool_e:
                    tool_counter.add(1,
                                     attributes={"tool": tool_name, "status": "error", "error": type(tool_e).__name__})
                    span.record_exception(tool_e)
                    span.set_attribute("tool.status", "error")
                    raise
            else:
                span.set_attribute("llm.direct_response", True)
                return data.get("response", "No response provided")

        except Exception as e:
            request_counter.add(1, attributes={"operation": "request_failed", "error": type(e).__name__})
            span.record_exception(e)
            span.set_status({"status_code": "ERROR", "description": str(e)})
            logger.error("study_agent_error", extra={"error": str(e), "input_preview": user_input[:100]})
            return f"Error: {str(e)}"

        finally:
            request_latency.record(time.time() - start_time, attributes={"agent": "study"})


def handle_request(user_input: str) -> str:
    result = run_agent(user_input)
    return str(result)