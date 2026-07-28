import os
import base64
import requests
from dotenv import load_dotenv

# 1. Загружаем переменные из файла .env (игнорирует всё лишнее)
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

print("="*60)
print("🎵 Тест прямого подключения к Spotify API")
print("="*60)

# Проверка наличия ключей
if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ ОШИБКА: Ключи SPOTIFY_CLIENT_ID или SPOTIFY_CLIENT_SECRET не найдены в .env файле!")
    print("💡 Проверьте, что файл .env лежит в папке microservices и в нём нет опечаток.")
    exit(1)

print(f"✅ Ключи найдены. Client ID: {CLIENT_ID[:5]}...{CLIENT_ID[-5:]}")

# 2. Получение токена (Client Credentials Flow)
print("\n🔄 Шаг 1: Запрос токена доступа...")
auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
b64_auth = base64.b64encode(auth_str.encode()).decode()

token_url = "https://accounts.spotify.com/api/token"
headers = {
    "Authorization": f"Basic {b64_auth}",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {"grant_type": "client_credentials"}

token_response = requests.post(token_url, headers=headers, data=data)

if token_response.status_code != 200:
    print(f"❌ ОШИБКА ПОЛУЧЕНИЯ ТОКЕНА: {token_response.status_code}")
    print(f"Ответ Spotify: {token_response.text}")
    print("💡 Частая причина: статус приложения в Spotify Dashboard не 'Active', или ключи скопированы с пробелами.")
    exit(1)

token_data = token_response.json()
access_token = token_data["access_token"]
print("✅ Токен успешно получен!")

# 3. Поиск трека
print("\n🔄 Шаг 2: Поиск трека 'The Killers'...")
search_url = "https://api.spotify.com/v1/search"
search_headers = {"Authorization": f"Bearer {access_token}"}
params = {"q": "The Killers", "type": "track", "limit": 1}

search_response = requests.get(search_url, headers=search_headers, params=params)

if search_response.status_code != 200:
    print(f"❌ ОШИБКА ПОИСКА: {search_response.status_code}")
    print(f"Ответ Spotify: {search_response.text}")
    exit(1)

search_data = search_response.json()
tracks = search_data.get("tracks", {}).get("items", [])

if not tracks:
    print("⚠️ Запрос прошел успешно, но Spotify вернул пустой список треков.")
else:
    track = tracks[0]
    print("✅ ПОИСК УСПЕШЕН! Получены реальные данные:")
    print(f"   🎵 Название: {track['name']}")
    print(f"   🎤 Исполнитель: {track['artists'][0]['name']}")
    print(f"   💿 Альбом: {track['album']['name']}")
    print(f"   🔗 Spotify ID: {track['id']}")

print("\n" + "="*60)
print("🎉 Тест завершен. Spotify API работает корректно!")
print("="*60)