import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Depends
import grpc

import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from api_gateway.schemas.playlists import (
    PlaylistCreate, PlaylistUpdate, TrackAdd,
    PlaylistResponse, MessageResponse,
)
from api_gateway.grpc_client import PlaylistGRPCClient
from shared.security import decode_access_token

log = logging.getLogger("gateway.playlists")
router = APIRouter(prefix="/playlists", tags=["playlists"])


def _current_user_id(authorization: Optional[str] = Header(None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = authorization[7:]
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        return int(payload["sub"])
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token payload")


def _map_grpc_error(e: grpc.RpcError) -> HTTPException:
    code = e.code()
    details = e.details()
    if code == grpc.StatusCode.NOT_FOUND:
        return HTTPException(status_code=404, detail=details)
    if code == grpc.StatusCode.PERMISSION_DENIED:
        return HTTPException(status_code=403, detail=details)
    if code in (grpc.StatusCode.ALREADY_EXISTS, grpc.StatusCode.FAILED_PRECONDITION):
        return HTTPException(status_code=409, detail=details)
    return HTTPException(status_code=503, detail=f"gRPC error: {details}")


def _to_pydantic(resp) -> PlaylistResponse:
    return PlaylistResponse(
        playlist_id=resp.playlist_id,
        owner_id=resp.owner_id,
        title=resp.title,
        description=resp.description,
        is_public=resp.is_public,
        tracks=[
            {
                "spotify_track_id": t.spotify_track_id,
                "position": t.position,
                "title": t.title if t.HasField("title") else None,
                "artist": t.artist if t.HasField("artist") else None,
            }
            for t in resp.tracks
        ],
    )


@router.post("", response_model=PlaylistResponse)
async def create_playlist(body: PlaylistCreate, user_id: int = Depends(_current_user_id)):
    client = PlaylistGRPCClient()
    try:
        resp = client.create_playlist(user_id, body.title, body.description or "", body.is_public)
        if not resp.success:
            raise HTTPException(status_code=400, detail=resp.message)
        return _to_pydantic(resp)
    except grpc.RpcError as e:
        raise _map_grpc_error(e)
    finally:
        client.close()


@router.get("/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(playlist_id: int, user_id: int = Depends(_current_user_id)):
    client = PlaylistGRPCClient()
    try:
        resp = client.get_playlist(playlist_id, user_id)
        if not resp.success:
            raise HTTPException(status_code=400, detail=resp.message)
        return _to_pydantic(resp)
    except grpc.RpcError as e:
        raise _map_grpc_error(e)
    finally:
        client.close()


@router.patch("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(playlist_id: int, body: PlaylistUpdate, user_id: int = Depends(_current_user_id)):
    client = PlaylistGRPCClient()
    try:
        resp = client.update_playlist(
            playlist_id, user_id,
            title=body.title, description=body.description, is_public=body.is_public,
        )
        if not resp.success:
            raise HTTPException(status_code=400, detail=resp.message)
        return _to_pydantic(resp)
    except grpc.RpcError as e:
        raise _map_grpc_error(e)
    finally:
        client.close()


@router.delete("/{playlist_id}", response_model=MessageResponse)
async def delete_playlist(playlist_id: int, user_id: int = Depends(_current_user_id)):
    client = PlaylistGRPCClient()
    try:
        resp = client.delete_playlist(playlist_id, user_id)
        return MessageResponse(success=resp.success, message=resp.message)
    except grpc.RpcError as e:
        raise _map_grpc_error(e)
    finally:
        client.close()


@router.post("/{playlist_id}/tracks", response_model=PlaylistResponse)
async def add_track(playlist_id: int, body: TrackAdd, user_id: int = Depends(_current_user_id)):
    client = PlaylistGRPCClient()
    try:
        resp = client.add_track(playlist_id, user_id, body.spotify_track_id, body.position)
        if not resp.success:
            raise HTTPException(status_code=400, detail=resp.message)
        return _to_pydantic(resp)
    except grpc.RpcError as e:
        raise _map_grpc_error(e)
    finally:
        client.close()


@router.delete("/{playlist_id}/tracks/{track_id}", response_model=PlaylistResponse)
async def remove_track(playlist_id: int, track_id: str, user_id: int = Depends(_current_user_id)):
    client = PlaylistGRPCClient()
    try:
        resp = client.remove_track(playlist_id, user_id, track_id)
        if not resp.success:
            raise HTTPException(status_code=400, detail=resp.message)
        return _to_pydantic(resp)
    except grpc.RpcError as e:
        raise _map_grpc_error(e)
    finally:
        client.close()


# Отдельный роутер для GET /users/{id}/playlists
user_playlists_router = APIRouter(tags=["playlists"])


@user_playlists_router.get("/users/{user_id}/playlists", response_model=list[PlaylistResponse])
async def list_user_playlists(user_id: int, request_user_id: int = Depends(_current_user_id)):
    client = PlaylistGRPCClient()
    try:
        resp = client.list_user_playlists(user_id, request_user_id)
        if not resp.success:
            raise HTTPException(status_code=400, detail=resp.message)
        return [_to_pydantic(p) for p in resp.playlists]
    except grpc.RpcError as e:
        raise _map_grpc_error(e)
    finally:
        client.close()