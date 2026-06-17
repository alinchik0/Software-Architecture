import logging
from typing import Optional, Dict

log = logging.getLogger("playlist-service.spotify")


class SpotifyClient:
    """Заглушка для получения метаданных треков из Spotify."""

    async def get_track_metadata(self, spotify_track_id: str) -> Optional[Dict[str, str]]:
        """
        Возвращает метаданные трека.
        В production здесь будет HTTP-запрос к Spotify Web API.
        """
        log.info(f"Fetching metadata for track {spotify_track_id} (stub)")
        return {
            "spotify_track_id": spotify_track_id,
            "title": f"Track {spotify_track_id}",
            "artist": "Unknown Artist",
        }

    async def close(self) -> None:
        log.info("SpotifyClient closed (stub)")