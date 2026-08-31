import logging
import grpc
from kafka_producer import kafka_producer
from typing import Optional
# Нужен для корректной обработки IntegrityError на уровне servicer
from sqlalchemy.exc import IntegrityError

from shared.database import async_session_factory
from playlist_service_logic import (
    create_playlist, get_playlist, update_playlist, delete_playlist,
    add_track, remove_track, list_user_playlists,
    PermissionDenied, NotFound,
)
from playlist_service.protos.generated import playlist_pb2, playlist_pb2_grpc

log = logging.getLogger("playlist-service.grpc")


def _fill_playlist_response(resp: playlist_pb2.PlaylistResponse, data: dict) -> None:
    resp.success = True
    resp.message = "ok"
    resp.playlist_id = data["playlist_id"]
    resp.owner_id = data["owner_id"]
    resp.title = data["title"]
    resp.description = data["description"]
    resp.is_public = data["is_public"]
    for t in data.get("tracks", []):
        tr = resp.tracks.add()
        tr.spotify_track_id = t["spotify_track_id"]
        tr.position = t["position"]
        if t.get("title") is not None:
            tr.title = t["title"]
        if t.get("artist") is not None:
            tr.artist = t["artist"]


def _set_error(context: grpc.ServicerContext, code: grpc.StatusCode, msg: str):
    context.set_code(code)
    context.set_details(msg)


class PlaylistServiceServicer(playlist_pb2_grpc.PlaylistServiceServicer):

    async def Ping(self, request, context):
        return playlist_pb2.PingResponse(message="pong from playlist-service")

    async def CreatePlaylist(self, request, context):
        try:
            async with async_session_factory() as db:
                data = await create_playlist(
                    db, request.owner_id, request.title, request.description, request.is_public
                )

                await kafka_producer.publish(
                    "playlist.created",
                    {"playlist_id": data["playlist_id"], "owner_id": data["owner_id"], "title": data["title"]}
                )

                resp = playlist_pb2.PlaylistResponse()
                _fill_playlist_response(resp, data)
                return resp
        except IntegrityError as e:
            _set_error(context, grpc.StatusCode.ALREADY_EXISTS, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))
        except Exception as e:
            log.exception("CreatePlaylist failed")
            _set_error(context, grpc.StatusCode.INTERNAL, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))

    async def GetPlaylist(self, request, context):
        try:
            async with async_session_factory() as db:
                data = await get_playlist(db, request.playlist_id, request.user_id)
                resp = playlist_pb2.PlaylistResponse()
                _fill_playlist_response(resp, data)
                return resp
        except NotFound as e:
            _set_error(context, grpc.StatusCode.NOT_FOUND, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))
        except PermissionDenied as e:
            _set_error(context, grpc.StatusCode.PERMISSION_DENIED, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))
        except Exception as e:
            log.exception("GetPlaylist failed")
            _set_error(context, grpc.StatusCode.INTERNAL, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))

    async def UpdatePlaylist(self, request, context):
        try:
            async with async_session_factory() as db:
                data = await update_playlist(
                    db, request.playlist_id, request.user_id, request.title, request.description, request.is_public
                )

                # ОТПРАВЛЯЕМ СОБЫТИЕ В KAFKA
                await kafka_producer.publish(
                    "playlist.updated",
                    {
                        "playlist_id": data["playlist_id"],
                        "user_id": data["owner_id"],
                        "title": data["title"]
                    }
                )

                resp = playlist_pb2.PlaylistResponse()
                _fill_playlist_response(resp, data)
                return resp
        except NotFound as e:
            _set_error(context, grpc.StatusCode.NOT_FOUND, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))
        except PermissionDenied as e:
            _set_error(context, grpc.StatusCode.PERMISSION_DENIED, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))
        except Exception as e:
            log.exception("UpdatePlaylist failed")
            _set_error(context, grpc.StatusCode.INTERNAL, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))

    async def DeletePlaylist(self, request, context):
        try:
            async with async_session_factory() as db:
                await delete_playlist(db, request.playlist_id, request.user_id)
                await kafka_producer.publish(
                    "playlist.deleted",
                    {
                        "playlist_id": request.playlist_id,
                        "user_id": request.user_id
                    }
                )

                return playlist_pb2.MessageResponse(success=True, message="deleted")
        except NotFound as e:
            _set_error(context, grpc.StatusCode.NOT_FOUND, str(e))
            return playlist_pb2.MessageResponse(success=False, message=str(e))
        except PermissionDenied as e:
            _set_error(context, grpc.StatusCode.PERMISSION_DENIED, str(e))
            return playlist_pb2.MessageResponse(success=False, message=str(e))
        except Exception as e:
            log.exception("DeletePlaylist failed")
            _set_error(context, grpc.StatusCode.INTERNAL, str(e))
            return playlist_pb2.MessageResponse(success=False, message=str(e))
    async def AddTrack(self, request, context):
        try:
            async with async_session_factory() as db:
                data = await add_track(
                    db, request.playlist_id, request.user_id,
                    request.spotify_track_id, request.position
                )

                # ОТПРАВЛЯЕМ СОБЫТИЕ В KAFKA
                await kafka_producer.publish(
                    "track.added",
                    {
                        "playlist_id": request.playlist_id,
                        "user_id": request.user_id,
                        "spotify_track_id": request.spotify_track_id,
                        "position": request.position
                    }
                )

                resp = playlist_pb2.PlaylistResponse()
                _fill_playlist_response(resp, data)
                return resp
        except NotFound as e:
            _set_error(context, grpc.StatusCode.NOT_FOUND, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))
        except PermissionDenied as e:
            _set_error(context, grpc.StatusCode.PERMISSION_DENIED, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))
        except ValueError as e:
            _set_error(context, grpc.StatusCode.ALREADY_EXISTS, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))
        except Exception as e:
            log.exception("AddTrack failed")
            _set_error(context, grpc.StatusCode.INTERNAL, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))

    async def RemoveTrack(self, request, context):
        try:
            async with async_session_factory() as db:
                data = await remove_track(
                    db, request.playlist_id, request.user_id, request.spotify_track_id
                )

                await kafka_producer.publish(
                    "track.removed",
                    {
                        "playlist_id": request.playlist_id,
                        "user_id": request.user_id,
                        "spotify_track_id": request.spotify_track_id
                    }
                )

                resp = playlist_pb2.PlaylistResponse()
                _fill_playlist_response(resp, data)
                return resp
        except NotFound as e:
            _set_error(context, grpc.StatusCode.NOT_FOUND, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))
        except PermissionDenied as e:
            _set_error(context, grpc.StatusCode.PERMISSION_DENIED, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))
        except Exception as e:
            log.exception("RemoveTrack failed")
            _set_error(context, grpc.StatusCode.INTERNAL, str(e))
            return playlist_pb2.PlaylistResponse(success=False, message=str(e))

    async def ListUserPlaylists(self, request, context):
        try:
            async with async_session_factory() as db:
                items = await list_user_playlists(db, request.user_id, request.request_user_id)
                resp = playlist_pb2.ListUserPlaylistsResponse(success=True, message="ok")
                for data in items:
                    p = resp.playlists.add()
                    _fill_playlist_response(p, data)
                return resp
        except Exception as e:
            log.exception("ListUserPlaylists failed")
            _set_error(context, grpc.StatusCode.INTERNAL, str(e))
            return playlist_pb2.ListUserPlaylistsResponse(success=False, message=str(e))


