"""
Диагностический скрипт для выявления проблем в работе LLM.
Показывает сырые ответы от модели и места, где падает парсинг.

Запуск: python diagnose_llm.py

Перед запуском:
1. ollama serve
2. uvicorn api.app:app --reload
"""

import requests
import time
import json
import sys

FASTAPI_URL = "http://127.0.0.1:8000"
OLLAMA_URL = "http://127.0.0.1:11434"
MODEL_NAME = "qwen3.5:4b-q4_K_M"

# Очень большой таймаут - ждём сколько нужно
LONG_TIMEOUT = 600  # 10 минут


def print_header(text):
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}")


def print_section(text):
    print(f"\n--- {text} ---")


def test_ollama_direct_simple():
    """Тест 1: Простейший запрос к Ollama без JSON."""
    print_header("ТЕСТ 1: Прямой запрос к Ollama (без JSON)")

    query = "Привет! Как тебя зовут?"
    print(f"Запрос: {query}")
    print(f"Модель: {MODEL_NAME}")
    print(f"Таймаут: {LONG_TIMEOUT} сек")
    print("\n⏳ Ожидаю ответа (может занять несколько минут)...")

    try:
        start = time.time()
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": query}],
                "stream": False
            },
            timeout=LONG_TIMEOUT
        )
        elapsed = time.time() - start

        print(f"\n✓ Ответ получен за {elapsed:.2f} сек")
        print(f"HTTP статус: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            content = data.get("message", {}).get("content", "")

            print_section("СЫРОЙ ОТВЕТ ОТ LLM")
            print(content)
            print_section("КОНЕЦ ОТВЕТА")

            return True, content
        else:
            print(f"✗ Ошибка HTTP {response.status_code}")
            print(f"Ответ: {response.text}")
            return False, None

    except requests.exceptions.Timeout:
        print(f"\n✗ Таймаут! LLM не ответила за {LONG_TIMEOUT} сек")
        return False, None
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        return False, None


def test_ollama_json_mode():
    """Тест 2: Запрос к Ollama с требованием JSON."""
    print_header("ТЕСТ 2: Запрос к Ollama с форматом JSON")

    system_prompt = "Ты маршрутизатор. Ответь строго в JSON формате: {\"route\": \"notes\"} или {\"route\": \"study\"}"
    user_query = "Добавь заметку: купить молоко завтра"

    print(f"System prompt: {system_prompt}")
    print(f"User query: {user_query}")
    print(f"Модель: {MODEL_NAME}")
    print(f"Параметр format: json")
    print("\n⏳ Ожидаю ответа...")

    try:
        start = time.time()
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                "stream": False,
                "format": "json"  # Принуждаем к JSON
            },
            timeout=LONG_TIMEOUT
        )
        elapsed = time.time() - start

        print(f"\n✓ Ответ получен за {elapsed:.2f} сек")

        if response.status_code == 200:
            data = response.json()
            content = data.get("message", {}).get("content", "")

            print_section("СЫРОЙ ОТВЕТ ОТ LLM")
            print(repr(content))  # repr показывает спецсимволы
            print_section("КОНЕЦ ОТВЕТА")

            # Пытаемся распарсить JSON
            print("\n🔍 Попытка парсинга JSON...")
            try:
                parsed = json.loads(content)
                print(f"✓ JSON успешно распарсен: {parsed}")
                return True, parsed
            except json.JSONDecodeError as e:
                print(f"✗ Ошибка парсинга JSON: {e}")
                print(f"  Строка: {repr(content)}")
                return False, content

        else:
            print(f"✗ Ошибка HTTP {response.status_code}")
            return False, None

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        return False, None


def test_fastapi_endpoint():
    """Тест 3: Запрос через FastAPI."""
    print_header("ТЕСТ 3: Запрос через FastAPI")

    # Сначала проверим доступные эндпоинты
    print("Проверяю доступные эндпоинты FastAPI...")
    try:
        response = requests.get(f"{FASTAPI_URL}/openapi.json", timeout=5)
        if response.status_code == 200:
            schema = response.json()
            paths = list(schema.get("paths", {}).keys())
            print(f"Доступные эндпоинты: {paths}")

            # Ищем эндпоинт для чата
            chat_endpoint = None
            for path in paths:
                if "chat" in path or "ask" in path or "query" in path:
                    chat_endpoint = path
                    break

            if not chat_endpoint:
                print("✗ Не найден эндпоинт для чата")
                return False

            print(f"Использую эндпоинт: {chat_endpoint}")

            # Проверяем схему запроса
            endpoint_schema = schema["paths"][chat_endpoint]["post"]
            request_body = endpoint_schema.get("requestBody", {})
            print(f"Схема запроса: {json.dumps(request_body, indent=2, ensure_ascii=False)[:500]}")

        else:
            print(f"✗ Не удалось получить схему API")
            return False

    except Exception as e:
        print(f"✗ Ошибка при получении схемы: {e}")
        return False

    # Теперь делаем реальный запрос
    query = "Добавь заметку: тестовая задача"
    print(f"\nОтправляю запрос: {query}")
    print("⏳ Ожидаю ответа...")

    try:
        start = time.time()
        response = requests.post(
            f"{FASTAPI_URL}{chat_endpoint}",
            json={"message": query},  # Пробуем поле "message"
            timeout=LONG_TIMEOUT
        )
        elapsed = time.time() - start

        print(f"\n✓ Ответ получен за {elapsed:.2f} сек")
        print(f"HTTP статус: {response.status_code}")

        print_section("СЫРОЙ ОТВЕТ ОТ FASTAPI")
        print(response.text)
        print_section("КОНЕЦ ОТВЕТА")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\n✓ Ответ успешно распарсен как JSON")
                print(f"Данные: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return True
            except json.JSONDecodeError as e:
                print(f"\n✗ Ответ не является валидным JSON: {e}")
                return False
        else:
            print(f"\n✗ Ошибка HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        return False


def test_notes_agent_directly():
    """Тест 4: Прямой вызов notes_agent (в обход FastAPI)."""
    print_header("ТЕСТ 4: Прямой вызов notes_agent")

    print("Импортирую notes_agent...")
    try:
        # Добавляем путь к проекту
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        from notes_agent.agent import handle_request

        query = "Добавь заметку: купить молоко завтра"
        print(f"Запрос: {query}")
        print("⏳ Вызываю handle_request (может занять несколько минут)...")

        start = time.time()
        result = handle_request(query)
        elapsed = time.time() - start

        print(f"\n✓ Ответ получен за {elapsed:.2f} сек")

        print_section("РЕЗУЛЬТАТ ОТ notes_agent")
        print(result)
        print_section("КОНЕЦ РЕЗУЛЬТАТА")

        return True

    except ImportError as e:
        print(f"✗ Не удалось импортировать notes_agent: {e}")
        print("  Убедись, что ты запускаешь скрипт из корня проекта mas/")
        return False
    except Exception as e:
        print(f"\n✗ Ошибка при вызове notes_agent: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*70)
    print("  ДИАГНОСТИКА ПРОБЛЕМ С LLM")
    print("="*70)
    print(f"Модель: {MODEL_NAME}")
    print(f"Ollama: {OLLAMA_URL}")
    print(f"FastAPI: {FASTAPI_URL}")
    print(f"Таймаут: {LONG_TIMEOUT} сек (10 минут)")

    results = {}

    # Тест 1: Простой запрос
    success, content = test_ollama_direct_simple()
    results["Ollama (простой)"] = success

    if not success:
        print("\n⛔ LLM не отвечает даже на простые запросы. Дальнейшие тесты бессмысленны.")
        sys.exit(1)

    # Тест 2: JSON режим
    success, parsed = test_ollama_json_mode()
    results["Ollama (JSON)"] = success

    # Тест 3: FastAPI
    success = test_fastapi_endpoint()
    results["FastAPI"] = success

    # Тест 4: Прямой вызов агента
    success = test_notes_agent_directly()
    results["notes_agent (прямой)"] = success

    # Итоговый отчёт
    print_header("ИТОГОВЫЙ ОТЧЁТ")
    for name, passed in results.items():
        status = "✓ OK" if passed else "✗ FAIL"
        print(f"  {status}  {name}")

    print("\n💡 АНАЛИЗ:")
    if results["Ollama (простой)"] and not results["Ollama (JSON)"]:
        print("  • LLM отвечает, но не возвращает валидный JSON")
        print("  • Проблема в промпте или парсинге ответа")

    if results["Ollama (JSON)"] and not results["FastAPI"]:
        print("  • LLM работает, но FastAPI ломает ответ")
        print("  • Проблема в коде FastAPI или оркестратора")

    if results["FastAPI"] and not results["notes_agent (прямой)"]:
        print("  • FastAPI работает, но прямой вызов агента падает")
        print("  • Проблема в самом агенте")

    print()


if __name__ == "__main__":
    main()