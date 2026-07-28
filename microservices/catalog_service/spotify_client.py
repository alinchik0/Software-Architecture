# # microservices/catalog_service/spotify_client.py
#
# import httpx
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# class SpotifyClient:
# 	"""
# 	Клиент для Deezer API (бесплатный, без ключей).
# 	Название класса оставлено для обратной совместимости с остальным кодом.
# 	"""
# 	BASE_URL = "https://api.deezer.com"
#
# 	def __init__(self):
# 		# Deezer не требует аутентификации для базовых запросов
# 		pass
#
# 	def _normalize_track(self, item: dict) -> dict:
# 		"""Приводит ответ Deezer к единому формату"""
# 		return {
# 			"id": str(item["id"]),  # Deezer возвращает числовой ID, конвертируем в строку
# 			"title": item.get("title", "Unknown"),
# 			"artist": item["artist"]["name"] if item.get("artist") else "Unknown Artist",
# 			"album": item["album"]["title"] if item.get("album") else "Unknown Album",
# 			"genre": "Unknown",  # Deezer не отдает жанр в поиске напрямую
# 			"cover": item["album"].get("cover_medium") if item.get("album") else None,
# 			"preview": item.get("preview"),  # 30-секундное MP3 превью!
# 		}
#
# 	async def get_track(self, track_id: str) -> dict | None:
# 		"""Получить метаданные трека по ID"""
# 		try:
# 			async with httpx.AsyncClient(timeout=10.0) as client:
# 				response = await client.get(f"{self.BASE_URL}/track/{track_id}")
# 				if response.status_code == 404:
# 					return None
# 				if response.status_code != 200:
# 					logger.error(f"Deezer Get Track Error {response.status_code}: {response.text}")
# 					return None
# 				return self._normalize_track(response.json())
# 		except Exception as e:
# 			logger.error(f"Error fetching track {track_id}: {e}")
# 			return None
#
# 	async def search_tracks(self, query: str, limit: int = 10) -> list:
# 		"""Поиск треков по названию или исполнителю"""
# 		try:
# 			async with httpx.AsyncClient(timeout=10.0) as client:
# 				response = await client.get(
# 					f"{self.BASE_URL}/search",
# 					params={"q": query, "limit": min(limit, 50)}
# 				)
# 				if response.status_code != 200:
# 					logger.error(f"Deezer Search Error {response.status_code}: {response.text}")
# 					return []
#
# 				data = response.json()
# 				items = data.get("data", [])
# 				logger.info(f"Deezer search for '{query}': found {len(items)} tracks")
# 				return [self._normalize_track(item) for item in items]
# 		except Exception as e:
# 			logger.error(f"Error searching tracks: {e}")
# 			return []
#
#
# # Глобальный экземпляр
# spotify_client = SpotifyClient()

# microservices/catalog_service/jamendo_client.py

import httpx
import logging
from config import settings

logger = logging.getLogger(__name__)


class JamendoClient:
	BASE_URL = "https://api.jamendo.com/v3.0"

	def __init__(self):
		self.client_id = settings.JAMENDO_CLIENT_ID

	def _normalize_track(self, item: dict) -> dict:
		"""Приводит ответ Jamendo к единому формату, который ожидает наш gRPC"""
		return {
			"id": str(item["id"]),
			"title": item.get("name", "Unknown"),
			"artist": item.get("artist_name", "Unknown Artist"),
			"album": item.get("album_name", "Unknown Album"),
			# Jamendo иногда вкладывает жанр в musicinfo, но это не всегда гарантировано
			"genre": item.get("musicinfo", {}).get("genre", "Unknown") if item.get("musicinfo") else "Unknown",
			"cover": item.get("image", None),
			# ВАЖНО: Jamendo отдает прямую ссылку на полный MP3 трек в поле 'audio'
			"preview": item.get("audio", None)
		}

	async def get_track(self, track_id: str) -> dict | None:
		"""Получить метаданные трека по ID"""
		try:
			async with httpx.AsyncClient(timeout=10.0) as client:
				response = await client.get(
					f"{self.BASE_URL}/tracks/",
					params={
						"client_id": self.client_id,
						"format": "json",
						"id": track_id,
						"audioformat": "mp32"  # mp32 = 320kbps, mp31 = 128kbps
					}
				)
				if response.status_code != 200:
					logger.error(f"Jamendo Get Track Error: {response.text}")
					return None

				data = response.json()
				results = data.get("results", [])
				if not results:
					return None

				return self._normalize_track(results[0])
		except Exception as e:
			logger.error(f"Error fetching track {track_id}: {e}")
			return None

	async def search_tracks(self, query: str, limit: int = 10) -> list:
		"""Поиск треков по названию или исполнителю"""
		try:
			async with httpx.AsyncClient(timeout=10.0) as client:
				response = await client.get(
					f"{self.BASE_URL}/tracks/",
					params={
						"client_id": self.client_id,
						"format": "json",
						"search": query,
						"limit": limit,
						"audioformat": "mp32"
					}
				)
				if response.status_code != 200:
					logger.error(f"Jamendo Search Error: {response.text}")
					return []

				data = response.json()
				items = data.get("results", [])
				logger.info(f"Jamendo search for '{query}': found {len(items)} tracks")

				return [self._normalize_track(item) for item in items]
		except Exception as e:
			logger.error(f"Error searching tracks: {e}")
			return []


# Глобальный экземпляр
spotify_client = JamendoClient()