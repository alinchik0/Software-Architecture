# playlist-service/services.py
import json
from grpc import StatusCode
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from shared.events import KafkaProducer, build_event
from shared.models import Playlist, PlaylistTrack
from repositories import PlaylistRepository
from schemas import PlaylistCreate, PlaylistUpdate, TrackAdd
from spotify.client import SpotifyClient

class ServiceError(Exception):
    def __init__(self, code: StatusCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

class PlaylistServiceLogic:
    def __init__(self, session: AsyncSession, producer: KafkaProducer | None = None, spotify: SpotifyClient | None = None, cache=None) -> None:
        self.session = session
        self.repo = PlaylistRepository(session)
        self.producer = producer
        self.spotify = spotify or SpotifyClient()
        self.cache = cache

    async def _emit(self, event_type: str, playlist_id: str, payload: dict) -> None:
        if self.producer:
            await self.producer.publish("playlist.events", playlist_id, build_event(event_type, playlist_id, payload))

    def _can_read(self, playlist: Playlist, requester_id: str) -> bool:
        return playlist.is_public or str(playlist.owner_id) == requester_id

    def _require_owner(self, playlist: Playlist, requester_id: str) -> None:
        if str(playlist.owner_id) != requester_id:
            raise ServiceError(StatusCode.PERMISSION_DENIED, "owner access required")

    async def create(self, owner_id: str, data: PlaylistCreate) -> Playlist:
        playlist = await self.repo.create(owner_id, data.title, data.description, data.is_public)
        await self.session.commit()
        await self.session.refresh(playlist, ["tracks"])
        await self._emit("playlist.created", str(playlist.id), {"owner_id": owner_id, "title": playlist.title})
        return playlist

    async def get(self, playlist_id: str, requester_id: str) -> Playlist:
        if self.cache:
            cached = await self.cache.get(f"playlist:{playlist_id}")
            if cached:
                # Cache is advisory; DB is still consulted for authorization freshness.
                pass
        playlist = await self.repo.get(playlist_id)
        if not playlist or not self._can_read(playlist, requester_id):
            raise ServiceError(StatusCode.NOT_FOUND, "playlist not found")
        if self.cache:
            await self.cache.set(f"playlist:{playlist_id}", json.dumps(playlist_to_dict(playlist)), ex=600)
        return playlist

    async def update(self, playlist_id: str, requester_id: str, data: PlaylistUpdate) -> Playlist:
        playlist = await self.repo.get(playlist_id)
        if not playlist:
            raise ServiceError(StatusCode.NOT_FOUND, "playlist not found")
        self._require_owner(playlist, requester_id)
        if data.title is not None:
            playlist.title = data.title
        if data.description is not None:
            playlist.description = data.description
        if data.is_public is not None:
            playlist.is_public = data.is_public
        await self.session.commit()
        await self.session.refresh(playlist, ["tracks"])
        if self.cache:
            await self.cache.delete(f"playlist:{playlist_id}")
        await self._emit("playlist.updated", playlist_id, {"is_public": playlist.is_public})
        return playlist

    async def delete(self, playlist_id: str, requester_id: str) -> None:
        playlist = await self.repo.get(playlist_id)
        if not playlist:
            raise ServiceError(StatusCode.NOT_FOUND, "playlist not found")
        self._require_owner(playlist, requester_id)
        await self.session.delete(playlist)
        await self.session.commit()
        if self.cache:
            await self.cache.delete(f"playlist:{playlist_id}")
        await self._emit("playlist.deleted", playlist_id, {})

    async def add_track(self, playlist_id: str, requester_id: str, data: TrackAdd) -> PlaylistTrack:
        playlist = await self.repo.get(playlist_id)
        if not playlist:
            raise ServiceError(StatusCode.NOT_FOUND, "playlist not found")
        self._require_owner(playlist, requester_id)
        if await self.repo.get_track(playlist_id, data.spotify_track_id):
            raise ServiceError(StatusCode.ALREADY_EXISTS, "track already exists")
        await self.spotify.get_track(data.spotify_track_id)
        track = PlaylistTrack(playlist_id=playlist.id, spotify_track_id=data.spotify_track_id, position=data.position)
        self.session.add(track)
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ServiceError(StatusCode.ALREADY_EXISTS, "track already exists") from exc
        if self.cache:
            await self.cache.delete(f"playlist:{playlist_id}")
        await self._emit("playlist.track.added", playlist_id, {"spotify_track_id": data.spotify_track_id})
        return track

    async def remove_track(self, playlist_id: str, requester_id: str, spotify_track_id: str) -> None:
        playlist = await self.repo.get(playlist_id)
        if not playlist:
            raise ServiceError(StatusCode.NOT_FOUND, "playlist not found")
        self._require_owner(playlist, requester_id)
        track = await self.repo.get_track(playlist_id, spotify_track_id)
        if not track:
            raise ServiceError(StatusCode.NOT_FOUND, "track not found")
        await self.session.delete(track)
        await self.session.commit()
        if self.cache:
            await self.cache.delete(f"playlist:{playlist_id}")
        await self._emit("playlist.track.removed", playlist_id, {"spotify_track_id": spotify_track_id})

    async def list_user(self, user_id: str, requester_id: str, visibility: str) -> list[Playlist]:
        if visibility not in {"public", "private", "all"}:
            raise ServiceError(StatusCode.INVALID_ARGUMENT, "invalid visibility")
        actual = visibility
        if user_id != requester_id:
            actual = "public"
        return await self.repo.list_for_user(user_id, actual)

def track_to_dict(track: PlaylistTrack) -> dict:
    return {"playlist_id": str(track.playlist_id), "spotify_track_id": track.spotify_track_id, "position": track.position, "added_at": str(track.added_at), "metadata": {}}

def playlist_to_dict(playlist: Playlist) -> dict:
    return {"id": str(playlist.id), "owner_id": str(playlist.owner_id), "title": playlist.title, "description": playlist.description or "", "is_public": playlist.is_public, "created_at": str(playlist.created_at), "updated_at": str(playlist.updated_at), "tracks": [track_to_dict(t) for t in playlist.tracks]}
