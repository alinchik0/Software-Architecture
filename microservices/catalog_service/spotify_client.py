import httpx
import base64
import logging
from config import settings

logger = logging.getLogger(__name__)


class SpotifyClient:
	def __init__(self):
		self.client_id = settings.SPOTIFY_CLIENT_ID
		self.client_secret = settings.SPOTIFY_CLIENT_SECRET
		self._access_token = None
		self._token_expires_at = 0

	async def _ensure_token(self):
		import time
		if self._access_token and time.time() < self._token_expires_at:
			return self._access_token

		auth_str = f"{self.client_id}:{self.client_secret}"
		b64_auth = base64.b64encode(auth_str.encode()).decode()

		async with httpx.AsyncClient() as client:
			response = await client.post(
				"https://accounts.spotify.com/api/token",
				headers={
					"Authorization": f"Basic {b64_auth}",
					"Content-Type": "application/x-www-form-urlencoded"
				},
				data={"grant_type": "client_credentials"}
			)
			response.raise_for_status()
			data = response.json()
			self._access_token = data["access_token"]
			# Spotify возвращает время жизни в секундах, оставляем запас 60 сек
			self._token_expires_at = time.time() + data["expires_in"] - 60
			return self._access_token

	async def get_track(self, track_id: str) -> dict | None:
		token = await self._ensure_token()
		async with httpx.AsyncClient() as client:
			response = await client.get(
				f"https://api.spotify.com/v1/tracks/{track_id}",
				headers={"Authorization": f"Bearer {token}"}
			)
			if response.status_code == 404:
				return None
			response.raise_for_status()
			data = response.json()

			# Примечание: Spotify API не возвращает жанр в объекте трека, только в объекте артиста.
			# Для упрощения и скорости оставляем "Unknown" или базовый жанр.
			return {
				"id": data["id"],
				"title": data["name"],
				"artist": data["artists"][0]["name"] if data["artists"] else "Unknown Artist",
				"album": data["album"]["name"],
				"genre": "Unknown"
			}

	async def search_tracks(self, query: str, limit: int = 5) -> list:
		token = await self._ensure_token()
		async with httpx.AsyncClient() as client:
			response = await client.get(
				f"https://api.spotify.com/v1/search",
				headers={"Authorization": f"Bearer {token}"},
				params={"q": query, "type": "track", "limit": limit}
			)
			response.raise_for_status()
			data = response.json()

			tracks = []
			for item in data["tracks"]["items"]:
				tracks.append({
					"id": item["id"],
					"title": item["name"],
					"artist": item["artists"][0]["name"] if item["artists"] else "Unknown",
					"album": item["album"]["name"],
					"genre": "Unknown"
				})
			return tracks


spotify_client = SpotifyClient()