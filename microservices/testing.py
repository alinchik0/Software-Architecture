# testing.py
"""
Простой скрипт для проверки работы модуля аутентификации.
Запускает последовательность запросов: регистрация → логин → logout.
"""
import httpx
import time
import sys

BASE_URL = "http://localhost:8000"

# Уникальный email для каждого запуска (чтобы не было конфликтов)
UNIQUE_EMAIL = f"test_{int(time.time())}@example.com"
PASSWORD = "SecurePassword123!"


def print_header(title: str):
	"""Красивый заголовок для теста."""
	print(f"\n{'=' * 60}")
	print(f"  {title}")
	print(f"{'=' * 60}")


def print_result(success: bool, message: str, data: dict = None):
	"""Выводит результат теста."""
	status = "✅ PASS" if success else "❌ FAIL"
	print(f"\n{status}: {message}")
	if data:
		print(f"  Response: {data}")
	return success


def test_register(client: httpx.Client, email: str, password: str) -> bool:
	"""Тест 1: Регистрация нового пользователя."""
	print_header("TEST 1: Регистрация пользователя")
	print(f"  Email: {email}")
	print(f"  Password: {password[:4]}***")

	response = client.post(
		f"{BASE_URL}/auth/register",
		json={"email": email, "password": password}
	)

	data = response.json()
	success = (
			response.status_code == 200
			and data.get("success") is True
			and data.get("user_id") is not None
	)

	return print_result(success, f"Статус {response.status_code}", data)


def test_register_duplicate(client: httpx.Client, email: str, password: str) -> bool:
	"""Тест 2: Попытка повторной регистрации (должна упасть)."""
	print_header("TEST 2: Повторная регистрация (ожидаем ошибку)")
	print(f"  Email: {email} (уже зарегистрирован)")

	response = client.post(
		f"{BASE_URL}/auth/register",
		json={"email": email, "password": password}
	)

	data = response.json()
	# Ожидаем, что регистрация не удалась
	success = (
			response.status_code == 200  # FastAPI возвращает 200, но success=False
			and data.get("success") is False
			and "already" in data.get("message", "").lower()
	)

	return print_result(success, f"Статус {response.status_code}", data)


def test_login_success(client: httpx.Client, email: str, password: str) -> str:
	"""Тест 3: Успешный логин. Возвращает токен."""
	print_header("TEST 3: Успешный логин")
	print(f"  Email: {email}")

	response = client.post(
		f"{BASE_URL}/auth/login",
		json={"email": email, "password": password}
	)

	data = response.json()
	success = (
			response.status_code == 200
			and "access_token" in data
			and data.get("user_id") is not None
	)

	print_result(success, f"Статус {response.status_code}", data)

	if success:
		token = data["access_token"]
		print(f"  Token (первые 50 символов): {token[:50]}...")
		return token
	return None


def test_login_wrong_password(client: httpx.Client, email: str) -> bool:
	"""Тест 4: Логин с неверным паролем (должен упасть)."""
	print_header("TEST 4: Логин с неверным паролем (ожидаем 401)")
	print(f"  Email: {email}")
	print(f"  Password: WrongPassword123!")

	response = client.post(
		f"{BASE_URL}/auth/login",
		json={"email": email, "password": "WrongPassword123!"}
	)

	data = response.json()
	success = response.status_code == 401

	return print_result(success, f"Статус {response.status_code}", data)


def test_login_nonexistent_user(client: httpx.Client) -> bool:
	"""Тест 5: Логин с несуществующим email (должен упасть)."""
	print_header("TEST 5: Логин с несуществующим email (ожидаем 401)")

	response = client.post(
		f"{BASE_URL}/auth/login",
		json={"email": "nonexistent@example.com", "password": "AnyPassword123!"}
	)

	data = response.json()
	success = response.status_code == 401

	return print_result(success, f"Статус {response.status_code}", data)


def test_login_invalid_email(client: httpx.Client) -> bool:
	"""Тест 6: Логин с невалидным email (должен упасть с 422)."""
	print_header("TEST 6: Логин с невалидным email (ожидаем 422)")

	response = client.post(
		f"{BASE_URL}/auth/login",
		json={"email": "not-an-email", "password": "Password123!"}
	)

	data = response.json()
	success = response.status_code == 422

	return print_result(success, f"Статус {response.status_code}", data)


def test_logout(client: httpx.Client, token: str) -> bool:
	"""Тест 7: Logout (добавление токена в blacklist)."""
	print_header("TEST 7: Logout")

	response = client.post(
		f"{BASE_URL}/auth/logout",
		headers={"Authorization": f"Bearer {token}"}
	)

	data = response.json()
	success = (
			response.status_code == 200
			and data.get("success") is True
	)

	return print_result(success, f"Статус {response.status_code}", data)


def test_health(client: httpx.Client) -> bool:
	"""Тест 8: Health check."""
	print_header("TEST 8: Health check")

	response = client.get(f"{BASE_URL}/health")
	data = response.json()
	success = response.status_code == 200 and data.get("status") == "ok"

	return print_result(success, f"Статус {response.status_code}", data)


def main():
	"""Запускает все тесты последовательно."""
	print("\n" + "=" * 60)
	print("  АВТОМАТИЧЕСКОЕ ТЕСТИРОВАНИЕ МОДУЛЯ АУТЕНТИФИКАЦИИ")
	print("=" * 60)
	print(f"  Base URL: {BASE_URL}")
	print(f"  Test email: {UNIQUE_EMAIL}")

	# Проверяем доступность сервера
	try:
		httpx.get(f"{BASE_URL}/health", timeout=3.0)
	except httpx.ConnectError:
		print(f"\n❌ ОШИБКА: Не удалось подключиться к {BASE_URL}")
		print("   Убедитесь, что api-gateway запущен:")
		print("   cd api_gateway && uvicorn main:app --port 8000")
		sys.exit(1)

	results = []

	# Используем синхронный клиент для простоты
	with httpx.Client(timeout=10.0) as client:
		# 1. Health check
		results.append(("Health check", test_health(client)))

		# 2. Регистрация
		results.append(("Регистрация", test_register(client, UNIQUE_EMAIL, PASSWORD)))

		# 3. Повторная регистрация (должна упасть)
		results.append(("Повторная регистрация", test_register_duplicate(client, UNIQUE_EMAIL, PASSWORD)))

		# 4. Успешный логин
		results.append(("Успешный логин", test_login_success(client, UNIQUE_EMAIL, PASSWORD) is not None))

		# 5. Логин с неверным паролем
		results.append(("Неверный пароль", test_login_wrong_password(client, UNIQUE_EMAIL)))

		# 6. Логин с несуществующим email
		results.append(("Несуществующий email", test_login_nonexistent_user(client)))

		# 7. Логин с невалидным email
		results.append(("Невалидный email", test_login_invalid_email(client)))

		# 8. Логин + logout
		token = test_login_success(client, UNIQUE_EMAIL, PASSWORD)
		if token:
			results.append(("Logout", test_logout(client, token)))
		else:
			print("\n⚠️  Пропускаем logout — не получили токен")
			results.append(("Logout", False))

	# Итоги
	print("\n" + "=" * 60)
	print("  ИТОГИ")
	print("=" * 60)

	passed = sum(1 for _, r in results if r)
	total = len(results)

	for name, result in results:
		status = "✅" if result else "❌"
		print(f"  {status} {name}")

	print(f"\n  Результат: {passed}/{total} тестов пройдено")

	if passed == total:
		print(" тесты пройдены успешно!")
	else:
		print(f"  {total - passed} тест(ов) не пройдено")

	return 0 if passed == total else 1


if __name__ == "__main__":
	sys.exit(main())