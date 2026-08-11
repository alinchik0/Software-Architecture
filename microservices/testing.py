import requests
import json

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "test_auto@music.com"
TEST_PASSWORD = "auto123456"
VALID_SPOTIFY_TRACK_ID = "3n3Ppam7vgaVa1iaRUc9Lp"


def print_step(step_name):
	print(f"\n{'=' * 50}\n▶ {step_name}\n{'=' * 50}")


def test_full_flow():
	headers = {}

	# 1. Регистрация и Вход
	print_step("1. Регистрация и получение JWT токена")
	reg_res = requests.post(f"{BASE_URL}/auth/register", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
	if reg_res.status_code not in [200, 201, 400]:
		print(f"❌ Ошибка регистрации: {reg_res.status_code} - {reg_res.text}")
		return

	login_res = requests.post(f"{BASE_URL}/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
	if login_res.status_code != 200:
		print(f"❌ Ошибка входа: {login_res.status_code} - {login_res.text}")
		return

	token = login_res.json().get("access_token")
	headers["Authorization"] = f"Bearer {token}"
	headers["Content-Type"] = "application/json"
	print("✅ Токен получен успешно.")

	# 2. Проверка поиска в каталоге (Самый важный шаг!)
	print_step("2. Поиск трека через Catalog Service (gRPC -> Spotify)")
	search_res = requests.get(f"{BASE_URL}/catalog/search?q=Killers&limit=3", headers=headers)
	if search_res.status_code != 200:
		print(f"❌ Ошибка поиска: {search_res.status_code} - {search_res.text}")
		print(
			"💡 Проверьте: 1) Подключен ли catalog_router в main.py, 2) Запущен ли catalog_service, 3) Верны ли ключи Spotify в .env")
	else:
		data = search_res.json()
		tracks = data.get("tracks", [])
		if not tracks:
			print("⚠️ Поиск вернул пустой список. Проверьте ключи Spotify или интернет-соединение.")
		else:
			print(f"✅ Поиск успешен! Найдено треков: {len(tracks)}")
			print(f"   Первый трек: {tracks[0]['title']} - {tracks[0]['artist']} (ID: {tracks[0]['id']})")

	# 3. Создание плейлиста
	print_step("3. Создание плейлиста")
	playlist_data = {"title": "Auto Test Playlist", "description": "Created by test script", "is_public": True}
	pl_res = requests.post(f"{BASE_URL}/playlists", headers=headers, json=playlist_data)
	if pl_res.status_code != 200:
		print(f"❌ Ошибка создания плейлиста: {pl_res.status_code} - {pl_res.text}")
		return

	playlist_id = pl_res.json().get("playlist_id")
	print(f"✅ Плейлист создан с ID: {playlist_id}")

	# 4. Добавление трека в плейлист
	print_step(f"4. Добавление трека (ID: {VALID_SPOTIFY_TRACK_ID}) в плейлист")
	add_track_data = {"spotify_track_id": VALID_SPOTIFY_TRACK_ID, "position": 1}
	add_res = requests.post(f"{BASE_URL}/playlists/{playlist_id}/tracks", headers=headers, json=add_track_data)
	if add_res.status_code != 200:
		print(f"❌ Ошибка добавления трека: {add_res.status_code} - {add_res.text}")
		print("💡 Убедитесь, что вы передаете именно ID (набор символов), а не полную URL-ссылку.")
	else:
		print("✅ Трек успешно добавлен!")


	print_step("5. Проверка: получение плейлиста с треками")
	get_pl_res = requests.get(f"{BASE_URL}/playlists/{playlist_id}", headers=headers)
	if get_pl_res.status_code != 200:
		print(f"❌ Ошибка получения плейлиста: {get_pl_res.status_code} - {get_pl_res.text}")
	else:
		pl_data = get_pl_res.json()
		tracks_in_pl = pl_data.get("tracks", [])
		print(f"✅ Плейлист получен. В нем {len(tracks_in_pl)} трек(ов).")
		for t in tracks_in_pl:
			print(f"   - {t.get('title')} by {t.get('artist')}")

	print_step("🎉 Тестирование завершено!")


if __name__ == "__main__":
	print("🚀 Запуск автоматизированного тестирования API...")
	print(
		"Убедитесь, что запущены: Docker (БД, Redis, Kafka), user_service, catalog_service, playlist_service, api_gateway")
	test_full_flow()