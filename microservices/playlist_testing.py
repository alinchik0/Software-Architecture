import requests
import json
import time

BASE_URL = "http://localhost:8000"


def print_response(response, test_name):
	"""Выводит результат теста"""
	status = "✅ PASS" if response.status_code in [200, 201, 204] else "❌ FAIL"
	print(f"\n{status} {test_name}")
	print(f"Status: {response.status_code}")
	try:
		print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
	except:
		print(f"Response: {response.text}")
	return response


def test_health_checks():
	"""Проверка health endpoints"""
	print("\n" + "=" * 60)
	print("ТЕСТ 1: Health Checks")
	print("=" * 60)

	r = requests.get(f"{BASE_URL}/health")
	print_response(r, "GET /health")

	r = requests.get(f"{BASE_URL}/ping/user")
	print_response(r, "GET /ping/user")

	r = requests.get(f"{BASE_URL}/ping/playlist")
	print_response(r, "GET /ping/playlist")


def test_auth():
	"""Регистрация и логин"""
	print("\n" + "=" * 60)
	print("ТЕСТ 2: Authentication")
	print("=" * 60)

	# Регистрация пользователя 1
	r = requests.post(f"{BASE_URL}/auth/register", json={
		"email": "user1@test.com",
		"password": "password123"
	})
	print_response(r, "POST /auth/register (user1)")

	# Логин пользователя 1
	r = requests.post(f"{BASE_URL}/auth/login", json={
		"email": "user1@test.com",
		"password": "password123"
	})
	resp = print_response(r, "POST /auth/login (user1)")
	user1_token = r.json().get("access_token") if r.status_code == 200 else None
	user1_id = r.json().get("user_id") if r.status_code == 200 else None

	# Регистрация пользователя 2
	r = requests.post(f"{BASE_URL}/auth/register", json={
		"email": "user2@test.com",
		"password": "password123"
	})
	print_response(r, "POST /auth/register (user2)")

	# Логин пользователя 2
	r = requests.post(f"{BASE_URL}/auth/login", json={
		"email": "user2@test.com",
		"password": "password123"
	})
	resp = print_response(r, "POST /auth/login (user2)")
	user2_token = r.json().get("access_token") if r.status_code == 200 else None
	user2_id = r.json().get("user_id") if r.status_code == 200 else None

	return user1_token, user1_id, user2_token, user2_id


def test_playlist_crud(user1_token, user1_id, user2_token, user2_id):
	"""CRUD операции с плейлистами"""
	print("\n" + "=" * 60)
	print("ТЕСТ 3: Playlist CRUD")
	print("=" * 60)

	headers1 = {"Authorization": f"Bearer {user1_token}"}
	headers2 = {"Authorization": f"Bearer {user2_token}"}

	# Создание плейлиста
	r = requests.post(f"{BASE_URL}/playlists", headers=headers1, json={
		"title": "My First Playlist",
		"description": "Test playlist",
		"is_public": True
	})
	resp = print_response(r, "POST /playlists (create)")
	playlist_id = r.json().get("playlist_id") if r.status_code in [200, 201] else None

	if not playlist_id:
		print("❌ Не удалось создать плейлист, пропускаем остальные тесты")
		return

	# Получение плейлиста
	r = requests.get(f"{BASE_URL}/playlists/{playlist_id}", headers=headers1)
	print_response(r, f"GET /playlists/{playlist_id}")

	# Обновление плейлиста
	r = requests.patch(f"{BASE_URL}/playlists/{playlist_id}", headers=headers1, json={
		"title": "Updated Playlist",
		"description": "Updated description"
	})
	print_response(r, f"PATCH /playlists/{playlist_id}")

	# Проверка прав доступа (user2 пытается редактировать)
	r = requests.patch(f"{BASE_URL}/playlists/{playlist_id}", headers=headers2, json={
		"title": "Hacked Playlist"
	})
	resp = print_response(r, f"PATCH /playlists/{playlist_id} (user2 - должен быть 403)")
	if r.status_code == 403:
		print("✅ Права доступа работают корректно")
	else:
		print("❌ Ошибка: должен быть 403 Forbidden")

	# Список плейлистов пользователя
	r = requests.get(f"{BASE_URL}/users/{user1_id}/playlists", headers=headers1)
	print_response(r, f"GET /users/{user1_id}/playlists")

	return playlist_id


def test_tracks(playlist_id, user1_token, user2_token):
	"""Работа с треками"""
	print("\n" + "=" * 60)
	print("ТЕСТ 4: Track Management")
	print("=" * 60)

	headers1 = {"Authorization": f"Bearer {user1_token}"}
	headers2 = {"Authorization": f"Bearer {user2_token}"}

	# Добавление трека
	r = requests.post(f"{BASE_URL}/playlists/{playlist_id}/tracks", headers=headers1, json={
		"spotify_track_id": "track_001",
		"position": 0
	})
	print_response(r, f"POST /playlists/{playlist_id}/tracks (add track)")

	# Добавление второго трека
	r = requests.post(f"{BASE_URL}/playlists/{playlist_id}/tracks", headers=headers1, json={
		"spotify_track_id": "track_002",
		"position": 1
	})
	print_response(r, f"POST /playlists/{playlist_id}/tracks (add second track)")

	# Проверка защиты от дубликатов
	r = requests.post(f"{BASE_URL}/playlists/{playlist_id}/tracks", headers=headers1, json={
		"spotify_track_id": "track_001",
		"position": 2
	})
	resp = print_response(r, f"POST /playlists/{playlist_id}/tracks (duplicate - должен быть 409)")
	if r.status_code == 409:
		print("✅ Защита от дубликатов работает")
	else:
		print("❌ Ошибка: должен быть 409 Conflict")

	# Проверка прав доступа (user2 пытается добавить трек)
	r = requests.post(f"{BASE_URL}/playlists/{playlist_id}/tracks", headers=headers2, json={
		"spotify_track_id": "track_003",
		"position": 2
	})
	resp = print_response(r, f"POST /playlists/{playlist_id}/tracks (user2 - должен быть 403)")
	if r.status_code == 403:
		print("✅ Права доступа для треков работают")
	else:
		print("❌ Ошибка: должен быть 403 Forbidden")

	# Получение плейлиста с треками
	r = requests.get(f"{BASE_URL}/playlists/{playlist_id}", headers=headers1)
	resp = print_response(r, f"GET /playlists/{playlist_id} (с треками)")
	tracks = r.json().get("tracks", [])
	if len(tracks) == 2:
		print(f"✅ В плейлисте {len(tracks)} трека")
	else:
		print(f"❌ Ожидается 2 трека, получено {len(tracks)}")

	# Удаление трека
	r = requests.delete(f"{BASE_URL}/playlists/{playlist_id}/tracks/track_001", headers=headers1)
	print_response(r, f"DELETE /playlists/{playlist_id}/tracks/track_001")

	# Проверка после удаления
	r = requests.get(f"{BASE_URL}/playlists/{playlist_id}", headers=headers1)
	resp = print_response(r, f"GET /playlists/{playlist_id} (после удаления)")
	tracks = r.json().get("tracks", [])
	if len(tracks) == 1:
		print(f"✅ В плейлисте {len(tracks)} трек после удаления")
	else:
		print(f"❌ Ожидается 1 трек, получено {len(tracks)}")


def test_cache(playlist_id, user1_token):
	"""Проверка кэширования"""
	print("\n" + "=" * 60)
	print("ТЕСТ 5: Cache Performance")
	print("=" * 60)

	headers = {"Authorization": f"Bearer {user1_token}"}

	# Первый запрос (должен быть медленнее)
	start = time.time()
	r = requests.get(f"{BASE_URL}/playlists/{playlist_id}", headers=headers)
	time1 = time.time() - start
	print(f"Первый запрос: {time1:.3f}s")

	# Второй запрос (должен быть быстрее из кэша)
	start = time.time()
	r = requests.get(f"{BASE_URL}/playlists/{playlist_id}", headers=headers)
	time2 = time.time() - start
	print(f"Второй запрос: {time2:.3f}s")

	if time2 < time1:
		print("✅ Кэширование работает (второй запрос быстрее)")
	else:
		print("⚠️  Кэширование может не работать или разница незначительна")

	# Обновление (должно инвалидировать кэш)
	r = requests.patch(f"{BASE_URL}/playlists/{playlist_id}", headers=headers, json={
		"title": "Cache Test Updated"
	})
	print_response(r, f"PATCH /playlists/{playlist_id} (invalidation)")

	# Запрос после обновления
	start = time.time()
	r = requests.get(f"{BASE_URL}/playlists/{playlist_id}", headers=headers)
	time3 = time.time() - start
	print(f"Запрос после обновления: {time3:.3f}s")


def test_delete_playlist(playlist_id, user1_token):
	"""Удаление плейлиста"""
	print("\n" + "=" * 60)
	print("ТЕСТ 6: Delete Playlist")
	print("=" * 60)

	headers = {"Authorization": f"Bearer {user1_token}"}

	r = requests.delete(f"{BASE_URL}/playlists/{playlist_id}", headers=headers)
	print_response(r, f"DELETE /playlists/{playlist_id}")

	# Проверка после удаления
	r = requests.get(f"{BASE_URL}/playlists/{playlist_id}", headers=headers)
	resp = print_response(r, f"GET /playlists/{playlist_id} (после удаления - должен быть 404)")
	if r.status_code == 404:
		print("✅ Плейлист успешно удалён")
	else:
		print("❌ Ошибка: должен быть 404 Not Found")


def test_logout(user1_token):
	"""Проверка logout"""
	print("\n" + "=" * 60)
	print("ТЕСТ 7: Logout")
	print("=" * 60)

	headers = {"Authorization": f"Bearer {user1_token}"}

	# Logout
	r = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
	print_response(r, "POST /auth/logout")

	# Попытка использовать токен после logout
	r = requests.get(f"{BASE_URL}/playlists", headers=headers)
	resp = print_response(r, "GET /playlists (после logout - должен быть 401)")
	if r.status_code == 401:
		print("✅ Logout работает корректно")
	else:
		print("❌ Ошибка: должен быть 401 Unauthorized")


if __name__ == "__main__":
	print("\n" + "=" * 60)
	print("ТЕСТИРОВАНИЕ PLAYLIST SERVICE")
	print("=" * 60)

	try:
		test_health_checks()
		user1_token, user1_id, user2_token, user2_id = test_auth()

		if not all([user1_token, user2_token]):
			print("\n❌ Не удалось получить токены, тестирование прервано")
			exit(1)

		playlist_id = test_playlist_crud(user1_token, user1_id, user2_token, user2_id)

		if playlist_id:
			test_tracks(playlist_id, user1_token, user2_token)
			test_cache(playlist_id, user1_token)
			test_delete_playlist(playlist_id, user1_token)

		test_logout(user1_token)

		print("\n" + "=" * 60)
		print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
		print("=" * 60)

	except requests.exceptions.ConnectionError:
		print("\n❌ Ошибка подключения к api-gateway")
		print("Убедись, что сервис запущен на http://localhost:8000")
	except Exception as e:
		print(f"\n❌ Непредвиденная ошибка: {e}")
		import traceback

		traceback.print_exc()