import requests
import time

ORCHESTRATOR_URL = "http://127.0.0.1:8000/chat"  # Убедись, что эндпоинт в api.py оркестратора именно /chat


def test_orchestrator(query, description):
	print(f"\n{'=' * 70}")
	print(f"ТЕСТ: {description}")
	print(f"Запрос: \"{query}\"")
	print(f"{'=' * 70}")

	start_time = time.time()
	try:
		# Оркестратор обычно принимает {"message": "..."} или {"input": "..."}
		# Проверь свой orchestrator/api.py. Если там Pydantic модель с полем 'message', оставь 'message'.
		response = requests.post(ORCHESTRATOR_URL, json={"message": query}, timeout=90)
		elapsed = time.time() - start_time

		print(f"⏱  Общее время: {elapsed:.2f} сек")
		print(f"📡 Статус HTTP: {response.status_code}")

		if response.status_code == 200:
			data = response.json()
			answer = data.get("response") or data.get("result") or str(data)
			print(f"\n✅ ОТВЕТ СИСТЕМЫ:")
			print("-" * 70)
			print(str(answer)[:800])
			if len(str(answer)) > 800:
				print("... [обрезано]")
			print("-" * 70)

			if elapsed < 15:
				print("🚀 ПОТРЯСАЮЩЕ! Вся мультиагентная система работает быстро.")
			else:
				print("⚠️  Система работает, но ответ занял >15 сек (возможно, cold start LLM).")
		else:
			print(f"❌ Ошибка: {response.text}")

	except requests.exceptions.Timeout:
		print("❌ Таймаут! Система не ответила за 90 секунд.")
	except requests.exceptions.ConnectionError:
		print("❌ Ошибка подключения! Убедись, что Orchestrator запущен на порту 8000.")
	except Exception as e:
		print(f"❌ Неожиданная ошибка: {e}")


if __name__ == "__main__":
	print("🚀 ЗАПУСК ПОЛНОГО ТЕСТА МУЛЬТИАГЕНТНОЙ СИСТЕМЫ 🚀\n")
	print("Убедись, что запущены ВСЕ три сервиса:")
	print("  1. Orchestrator (port 8000)")
	print("  2. Notes Agent (port 8001)")
	print("  3. Study Agent (port 8002)")
	input("\nНажми Enter, чтобы начать тест...")

	# Тест 1: Маршрутизация в Notes
	test_orchestrator(
		"Add a note: read chapter 5 of software architecture book tomorrow",
		"Маршрутизация в Notes Agent"
	)

	# Тест 2: Маршрутизация в Study
	test_orchestrator(
		"Explain the difference between monolithic and microservices architecture",
		"Маршрутизация в Study Agent"
	)

	# Тест 3: Проверка инструментов Study Agent (если запрос требует поиска)
	test_orchestrator(
		"Search for information about CAP theorem",
		"Вызов инструмента search_material в Study Agent"
	)