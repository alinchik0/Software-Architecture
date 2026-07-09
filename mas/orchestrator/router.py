# orchestrator/router.py
import logging
import requests
import json
from shared.observability import get_tracer

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "qwen3.5:4b-q4_K_M"


def route_request(user_input: str) -> str:
	with tracer.start_as_current_span("router_llm_call") as span:
		span.set_attributes({
			"gen_ai.system": "ollama",
			"gen_ai.request.model": MODEL_NAME,
			"operation": "route_classification"
		})

		prompt = open("orchestrator/prompts/router.md").read()
		payload = {
			"model": MODEL_NAME,
			"messages": [
				{"role": "system", "content": prompt},
				{"role": "user", "content": user_input}
			],
			"stream": False
		}

		response = requests.post(OLLAMA_URL, json=payload)
		data = response.json()
		content = data.get("message", {}).get("content", "")

		# 📝 Событие с превью ответа (не создаёт новый спан)
		span.add_event("llm_response_received", attributes={
			"response_preview": content[:200],
			"status_code": response.status_code
		})

		parsed = json.loads(content)  # Может упасть здесь
		route = parsed["route"]

		span.set_attribute("chosen_route", route)
		return route