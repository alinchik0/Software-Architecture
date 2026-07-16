# # orchestrator/router.py
# import logging
# import requests
# import json
# from shared.observability import get_tracer
#
# logger = logging.getLogger(__name__)
# tracer = get_tracer(__name__)
#
# OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
# MODEL_NAME = "qwen3.5:4b-q4_K_M"
#
#
# # def route_request(user_input: str) -> str:
# # 	with tracer.start_as_current_span("router_llm_call") as span:
# # 		span.set_attributes({
# # 			"gen_ai.system": "ollama",
# # 			"gen_ai.request.model": MODEL_NAME,
# # 			"operation": "route_classification"
# # 		})
# #
# # 		prompt = open("orchestrator/prompts/router.md").read()
# # 		payload = {
# # 			"model": MODEL_NAME,
# # 			"messages": [
# # 				{"role": "system", "content": prompt},
# # 				{"role": "user", "content": user_input}
# # 			],
# # 			"stream": False
# # 		}
# #
# # 		response = requests.post(OLLAMA_URL, json=payload)
# # 		data = response.json()
# # 		content = data.get("message", {}).get("content", "")
# #
# # 		# 📝 Событие с превью ответа (не создаёт новый спан)
# # 		span.add_event("llm_response_received", attributes={
# # 			"response_preview": content[:200],
# # 			"status_code": response.status_code
# # 		})
# #
# # 		parsed = json.loads(content)  # Может упасть здесь
# # 		route = parsed["route"]
# #
# # 		span.set_attribute("chosen_route", route)
# # 		return route
#
# from pathlib import Path
# from shared.llm_client import call_llm_json
#
# PROMPTS_DIR = Path(__file__).parent / "prompts"
#
#
# def route_request(user_message: str) -> str:
# 	"""Определяет, какому агенту передать запрос."""
# 	prompt = (PROMPTS_DIR / "router.md").read_text(encoding="utf-8")
#
# 	data = call_llm_json(
# 		system_prompt=prompt,
# 		user_prompt=user_message,
# 		timeout=30
# 	)
#
# 	if "error" in data:
# 		print(f"[Router] Ошибка: {data['error']}")
# 		return "study"  # Fallback
#
# 	route = data.get("route", "study")
# 	print(f"[Router] Выбран маршрут: {route}")
# 	return route

import logging
from pathlib import Path
from shared.llm_client import call_llm_json, HF_MODEL

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"


def route_request(user_message: str) -> str:
	"""
	Определяет, какому агенту передать запрос.
	Возвращает: "notes" или "study"
	"""
	try:
		# Читаем базовый промпт
		system_prompt = (PROMPTS_DIR / "router.md").read_text(encoding="utf-8")

		logger.info("Routing request via LLM", extra={"input_preview": user_message[:50]})

		# Вызываем LLM (таймаут 30 сек более чем достаточен для классификации)
		data = call_llm_json(
			system_prompt=system_prompt,
			user_prompt=user_message,
			timeout=30
		)

		# Обработка ошибок LLM
		if "error" in data:
			logger.warning(f"Router LLM error: {data['error']}. Defaulting to 'study'.")
			return "study"

		# Извлекаем маршрут
		route = data.get("route", "study").lower().strip()

		# Валидация
		if route not in ["notes", "study"]:
			logger.warning(f"Unknown route '{route}' from LLM. Defaulting to 'study'.")
			return "study"

		logger.info(f"Router successfully selected: {route}")
		return route

	except Exception as e:
		logger.error(f"Router failed with exception: {e}. Defaulting to 'study'.")
		return "study"