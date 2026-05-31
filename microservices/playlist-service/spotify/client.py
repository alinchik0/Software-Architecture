# playlist-service/spotify/client.py
import httpx
from shared.config import get_settings

class SpotifyClient:
    async def get_track(self, spotify_track_id: str) -> dict:
        settings = get_settings()
        if not settings.spotify_bearer_token:
            # ASSUMPTION: local development can run without Spotify credentials.
            return {"id": spotify_track_id, "source": "mock"}
        headers = {"Authorization": f"Bearer {settings.spotify_bearer_token}"}
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{settings.spotify_api_base_url}/tracks/{spotify_track_id}", headers=headers)
            response.raise_for_status()
            data = response.json()
            return {"id": data["id"], "name": data.get("name"), "artists": [a.get("name") for a in data.get("artists", [])]}
