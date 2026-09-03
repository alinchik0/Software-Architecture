import json
import logging
from typing import Optional, List

from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.playlist import Playlist, PlaylistTrack
from shared.redis_cache import redis_client
from playlist_service.catalog_client import catalog_client
from kafka_producer import kafka_producer
from config import PlaylistServiceSettings

log = logging.getLogger("playlist-service.logic")
cfg = PlaylistServiceSettings()



class PermissionDenied(Exception):
    pass


class NotFound(Exception):
    pass


def _cache_key(playlist_id: int) -> str:
    return f"playlist:{playlist_id}"


async def _invalidate_cache(playlist_id: int) -> None:
    try:
        await redis_client.delete(_cache_key(playlist_id))
    except Exception as e:
        log.warning(f"Cache invalidation failed: {e}")


async def _playlist_to_dict(pl: Playlist, tracks: List[PlaylistTrack]) -> dict:
    tracks_data = []
    for t in tracks:
        # ТЕПЕРЬ МЫ ИСПОЛЬЗУЕМ catalog_client ЧЕРЕЗ gRPC
        meta = await catalog_client.get_track_info(t.spotify_track_id)
        tracks_data.append({
            "spotify_track_id": t.spotify_track_id,
            "position": t.position,
            "title": meta.get("title") if meta else None,
            "artist": meta.get("artist") if meta else None,
        })
    return {
        "playlist_id": pl.id,
        "owner_id": pl.owner_id,
        "title": pl.title,
        "description": pl.description or "",
        "is_public": pl.is_public,
        "tracks": tracks_data,
    }


async def create_playlist(
    db: AsyncSession, owner_id: int, title: str, description: str, is_public: bool
) -> dict:
    pl = Playlist(owner_id=owner_id, title=title, description=description, is_public=is_public)
    db.add(pl)
    try:
        await db.commit()
        await db.refresh(pl)
    except IntegrityError as e:
        await db.rollback()
        raise

    # Инвалидируем кэш списка плейлистов пользователя
    try:
        await redis_client.delete(f"user_playlists:{owner_id}")
        log.info(f"Invalidated user playlists cache for: {owner_id}")
    except Exception as e:
        log.warning(f"Cache invalidation failed: {e}")

    return await _playlist_to_dict(pl, [])


# async def get_playlist(db: AsyncSession, playlist_id: int, user_id: int) -> dict:
#     pl = await db.get(Playlist, playlist_id)
#     if not pl:
#         raise NotFound(f"Playlist {playlist_id} not found")
#     if not pl.is_public and pl.owner_id != user_id:
#         raise PermissionDenied("Access denied")
#
#     stmt = select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id).order_by(PlaylistTrack.position)
#     res = await db.execute(stmt)
#     tracks = list(res.scalars().all())
#     return await _playlist_to_dict(pl, tracks)

async def get_playlist(db: AsyncSession, playlist_id: int, user_id: int) -> dict:
    # 1. Пытаемся получить из кэша
    cache_key = _cache_key(playlist_id)
    try:
        cached_data = await redis_client.get(cache_key)
        if cached_data:
            log.info(f"Cache hit for playlist {playlist_id}")
            return json.loads(cached_data)
    except Exception as e:
        log.warning(f"Redis cache read failed: {e}")

    # 2. Cache miss — запрашиваем из БД
    log.info(f"Cache miss for playlist {playlist_id}, fetching from DB")
    pl = await db.get(Playlist, playlist_id)
    if not pl:
        raise NotFound(f"Playlist {playlist_id} not found")
    if not pl.is_public and pl.owner_id != user_id:
        raise PermissionDenied("Access denied")

    stmt = select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id).order_by(PlaylistTrack.position)
    res = await db.execute(stmt)
    tracks = list(res.scalars().all())

    result = await _playlist_to_dict(pl, tracks)

    # 3. Сохраняем в кэш на 300 секунд (5 минут)
    try:
        await redis_client.setex(cache_key, 300, json.dumps(result))
        log.info(f"Playlist {playlist_id} cached for 300 seconds")
    except Exception as e:
        log.warning(f"Redis cache write failed: {e}")

    return result


async def update_playlist(
    db: AsyncSession, playlist_id: int, user_id: int,
    title: Optional[str], description: Optional[str], is_public: Optional[bool]
) -> dict:
    pl = await db.get(Playlist, playlist_id)
    if not pl:
        raise NotFound(f"Playlist {playlist_id} not found")
    if pl.owner_id != user_id:
        raise PermissionDenied("Only owner can update playlist")

    changed = {}
    if title is not None:
        pl.title = title
        changed["title"] = title
    if description is not None:
        pl.description = description
        changed["description"] = description
    if is_public is not None:
        pl.is_public = is_public
        changed["is_public"] = is_public

    await db.commit()
    await db.refresh(pl)

    stmt = select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id).order_by(PlaylistTrack.position)
    res = await db.execute(stmt)
    tracks = list(res.scalars().all())

    await _invalidate_cache(playlist_id)
    await kafka_producer.publish("playlist.updated", pl.id, user_id, changed)
    return await _playlist_to_dict(pl, tracks)


async def delete_playlist(db: AsyncSession, playlist_id: int, user_id: int) -> None:
    pl = await db.get(Playlist, playlist_id)
    if not pl:
        raise NotFound(f"Playlist {playlist_id} not found")
    if pl.owner_id != user_id:
        raise PermissionDenied("Only owner can delete playlist")

    await db.delete(pl)

    # Инвалидируем кэш списка плейлистов пользователя
    try:
        await redis_client.delete(f"user_playlists:{user_id}")
        log.info(f"Invalidated user playlists cache for: {user_id}")
    except Exception as e:
        log.warning(f"Cache invalidation failed: {e}")

    await db.commit()
    await _invalidate_cache(playlist_id)
    await kafka_producer.publish("playlist.deleted", playlist_id, user_id, {})


async def add_track(
    db: AsyncSession, playlist_id: int, user_id: int,
    spotify_track_id: str, position: int
) -> dict:
    pl = await db.get(Playlist, playlist_id)
    if not pl:
        raise NotFound(f"Playlist {playlist_id} not found")
    if pl.owner_id != user_id:
        raise PermissionDenied("Only owner can modify playlist")

    track = PlaylistTrack(
        playlist_id=playlist_id,
        spotify_track_id=spotify_track_id,
        position=position,
    )
    db.add(track)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError(f"Track {spotify_track_id} already exists in playlist {playlist_id}")

    stmt = select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id).order_by(PlaylistTrack.position)
    res = await db.execute(stmt)
    tracks = list(res.scalars().all())

    await _invalidate_cache(playlist_id)
    return await _playlist_to_dict(pl, tracks)


async def remove_track(db: AsyncSession, playlist_id: int, user_id: int, spotify_track_id: str) -> dict:
    pl = await db.get(Playlist, playlist_id)
    if not pl:
        raise NotFound(f"Playlist {playlist_id} not found")
    if pl.owner_id != user_id:
        raise PermissionDenied("Only owner can modify playlist")

    stmt = delete(PlaylistTrack).where(
        PlaylistTrack.playlist_id == playlist_id,
        PlaylistTrack.spotify_track_id == spotify_track_id,
    )
    res = await db.execute(stmt)
    if res.rowcount == 0:
        raise NotFound(f"Track {spotify_track_id} not found in playlist {playlist_id}")
    await db.commit()

    stmt = select(PlaylistTrack).where(PlaylistTrack.playlist_id == playlist_id).order_by(PlaylistTrack.position)
    res = await db.execute(stmt)
    tracks = list(res.scalars().all())

    await _invalidate_cache(playlist_id)
    return await _playlist_to_dict(pl, tracks)


# async def list_user_playlists(db: AsyncSession, user_id: int, request_user_id: int) -> List[dict]:
#     stmt = select(Playlist).where(Playlist.owner_id == user_id)
#     res = await db.execute(stmt)
#     playlists = list(res.scalars().all())
#
#     result = []
#     for pl in playlists:
#         if not pl.is_public and pl.owner_id != request_user_id:
#             continue
#         stmt_t = select(PlaylistTrack).where(PlaylistTrack.playlist_id == pl.id).order_by(PlaylistTrack.position)
#         res_t = await db.execute(stmt_t)
#         tracks = list(res_t.scalars().all())
#         result.append(await _playlist_to_dict(pl, tracks))
#     return result

async def list_user_playlists(db: AsyncSession, user_id: int, request_user_id: int) -> List[dict]:
    # 1. Проверяем кэш
    cache_key = f"user_playlists:{user_id}"
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            log.info(f"Cache hit for user playlists: {user_id}")
            return json.loads(cached)
    except Exception as e:
        log.warning(f"Redis cache read failed: {e}")

    # 2. Cache miss — запрашиваем из БД
    log.info(f"Cache miss for user playlists: {user_id}, fetching from DB")
    stmt = select(Playlist).where(Playlist.owner_id == user_id)
    res = await db.execute(stmt)
    playlists = list(res.scalars().all())

    result = []
    for pl in playlists:
        if not pl.is_public and pl.owner_id != request_user_id:
            continue
        stmt_t = select(PlaylistTrack).where(PlaylistTrack.playlist_id == pl.id).order_by(PlaylistTrack.position)
        res_t = await db.execute(stmt_t)
        tracks = list(res_t.scalars().all())
        result.append(await _playlist_to_dict(pl, tracks))

    # 3. Сохраняем в кэш на 5 минут
    try:
        await redis_client.setex(cache_key, 300, json.dumps(result))
        log.info(f"User playlists cached for 300 seconds: {user_id}")
    except Exception as e:
        log.warning(f"Redis cache write failed: {e}")

    return result