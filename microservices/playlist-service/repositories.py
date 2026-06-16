# playlist-service/repositories.py
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from shared.models import Playlist, PlaylistTrack

class PlaylistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, playlist_id: str) -> Playlist | None:
        stmt = select(Playlist).options(selectinload(Playlist.tracks)).where(Playlist.id == uuid.UUID(playlist_id))
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, owner_id: str, title: str, description: str | None, is_public: bool) -> Playlist:
        playlist = Playlist(owner_id=uuid.UUID(owner_id), title=title, description=description, is_public=is_public)
        self.session.add(playlist)
        await self.session.flush()
        return playlist

    async def list_for_user(self, user_id: str, visibility: str) -> list[Playlist]:
        stmt = select(Playlist).options(selectinload(Playlist.tracks)).where(Playlist.owner_id == uuid.UUID(user_id))
        if visibility == "public":
            stmt = stmt.where(Playlist.is_public.is_(True))
        elif visibility == "private":
            stmt = stmt.where(Playlist.is_public.is_(False))
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_track(self, playlist_id: str, track_id: str) -> PlaylistTrack | None:
        return await self.session.get(PlaylistTrack, {"playlist_id": uuid.UUID(playlist_id), "spotify_track_id": track_id})
