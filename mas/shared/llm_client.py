"""
LLM-клиент для мультиагентной системы.
Использует Hugging Face Inference API (бесплатно).
"""

import os
import json
import re
import time
import requests

try:
	from dotenv import load_dotenv

	load_dotenv()
except ImportError:
	pass

# ==========================================
# НАСТРОЙКИ
# ==========================================
HF_TOKEN = os.environ.get("HF_TOKEN", "")
HF_MODEL = os.environ.get("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")

# OpenAI-совместимый endpoint Hugging Face
HF_URL = "https://router.huggingface.co/v1/chat/completions"

# Максимальное число попыток при cold start
MAX_RETRIES = 3
RETRY_DELAY = 5  # секунд


# ==========================================
# ОСНОВНАЯ ФУНКЦИЯ
# ==========================================
def call_llm(
		system_prompt: str,
		user_prompt: str,
		temperature: float = 0.3,
		json_mode: bool = False,
		timeout: int = 90
) -> str:
	"""
	Отправляет запрос к LLM через Hugging Face Inference API.

	Примечание: бесплатные модели могут "засыпать" и "просыпаться" ~20-60 секунд.
	Это нормально — скрипт автоматически повторит запрос.
	"""

	headers = {
		"Authorization": f"Bearer {HF_TOKEN}",
		"Content-Type": "application/json"
	}

	payload = {
		"model": HF_MODEL,
		"messages": [
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": user_prompt}
		],
		"temperature": temperature,
		"max_tokens": 2048
	}

	# Hugging Face поддерживает JSON mode через response_format
	if json_mode:
		payload["response_format"] = {"type": "json_object"}

	for attempt in range(MAX_RETRIES):
		try:
			response = requests.post(
				HF_URL,
				headers=headers,
				json=payload,
				timeout=timeout,
				proxies = {"http": None, "https": None}
			)

			# Успех
			if response.status_code == 200:
				data = response.json()
				return data["choices"][0]["message"]["content"]

			# Модель загружается (cold start)
			if response.status_code == 503:
				print(f"[HF] Модель загружается... попытка {attempt + 1}/{MAX_RETRIES}")
				time.sleep(RETRY_DELAY)
				continue

			# Превышен лимит запросов
			if response.status_code == 429:
				return "Error: Rate limit exceeded. Подожди минуту."

			# Неверный токен
			if response.status_code == 401:
				return "Error: Invalid HF_TOKEN. Проверь .env файл."

			# Другие ошибки
			return f"Error: HTTP {response.status_code} - {response.text[:200]}"

		except requests.exceptions.Timeout:
			return f"Error: Timeout ({timeout}s)"
		except Exception as e:
			return f"Error: {e}"

	return "Error: Model failed to load after multiple attempts"


def call_llm_json(system_prompt: str, user_prompt: str, timeout: int = 90) -> dict:
	"""Вызывает LLM и парсит ответ как JSON."""
	content = call_llm(system_prompt, user_prompt, json_mode=True, timeout=timeout)

	if content.startswith("Error:"):
		return {"error": content}

	try:
		return json.loads(content)
	except json.JSONDecodeError:
		# Пытаемся извлечь JSON из текста
		match = re.search(r'\{.*?\}', content, re.DOTALL)
		if match:
			try:
				return json.loads(match.group(0))
			except:
				pass
		return {"error": f"Invalid JSON: {content[:200]}"}


# ==========================================
# ВЫЗОВ С ИНСТРУМЕНТАМИ (для Notes и Study агентов)
# ==========================================
def call_llm_with_tools(
		system_prompt: str,
		user_prompt: str,
		tools: list,
		temperature: float = 0.1,
		timeout: int = 90
) -> dict:
	"""
	Вызов LLM с поддержкой tools (function calling).
	Возвращает ответ в формате, совместимом с OpenAI API.
	"""
	headers = {
		"Authorization": f"Bearer {HF_TOKEN}",
		"Content-Type": "application/json"
	}

	payload = {
		"model": HF_MODEL,
		"messages": [
			{"role": "system", "content": system_prompt},
			{"role": "user", "content": user_prompt}
		],
		"tools": tools,
		"tool_choice": "auto",
		"temperature": temperature,
		"max_tokens": 2048
	}

	for attempt in range(MAX_RETRIES):
		try:
			response = requests.post(
				HF_URL,
				headers=headers,
				json=payload,
				timeout=timeout,
				proxies={"http": None, "https": None}  # Обход прокси
			)

			if response.status_code == 200:
				return response.json()

			if response.status_code == 503:
				print(f"[HF] Модель загружается (cold start)... попытка {attempt + 1}/{MAX_RETRIES}")
				time.sleep(RETRY_DELAY)
				continue

			if response.status_code == 429:
				return {"error": "Rate limit exceeded. Подожди минуту."}

			if response.status_code == 401:
				return {"error": "Invalid HF_TOKEN. Проверь .env файл."}

			return {"error": f"HTTP {response.status_code} - {response.text[:200]}"}

		except requests.exceptions.Timeout:
			return {"error": f"Timeout ({timeout}s)"}
		except Exception as e:
			return {"error": str(e)}

	return {"error": "Model failed to load after multiple attempts"}