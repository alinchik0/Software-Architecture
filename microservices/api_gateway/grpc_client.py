# api_gateway/grpc_client.py
import grpc
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from playlist_service.protos.generated import playlist_pb2, playlist_pb2_grpc
from user_service.protos.generated import auth_pb2, auth_pb2_grpc
from config import GatewaySettings

cfg = GatewaySettings()


class AuthGRPCClient:
	def __init__(self):
		self.channel = grpc.insecure_channel(cfg.USER_GRPC_URL)
		self.stub = auth_pb2_grpc.AuthServiceStub(self.channel)

	def close(self):
		"""Закрывает gRPC канал."""
		self.channel.close()

	def register(self, email: str, password: str):
		"""Вызывает gRPC метод Register."""
		request = auth_pb2.RegisterRequest(email=email, password=password)
		return self.stub.Register(request)

	def login(self, email: str, password: str):
		"""Вызывает gRPC метод Login."""
		request = auth_pb2.LoginRequest(email=email, password=password)
		return self.stub.Login(request)

	def logout(self, token: str):
		"""Вызывает gRPC метод Logout."""
		request = auth_pb2.LogoutRequest(token=token)
		return self.stub.Logout(request)



class PlaylistGRPCClient:
    def __init__(self):
        self.channel = grpc.insecure_channel(cfg.PLAYLIST_GRPC_URL)
        self.stub = playlist_pb2_grpc.PlaylistServiceStub(self.channel)

    def close(self):
        self.channel.close()

    def create_playlist(self, owner_id: int, title: str, description: str, is_public: bool):
        req = playlist_pb2.CreatePlaylistRequest(
            owner_id=owner_id, title=title, description=description, is_public=is_public
        )
        return self.stub.CreatePlaylist(req)

    def get_playlist(self, playlist_id: int, user_id: int):
        req = playlist_pb2.GetPlaylistRequest(playlist_id=playlist_id, user_id=user_id)
        return self.stub.GetPlaylist(req)

    def update_playlist(self, playlist_id: int, user_id: int,
                        title=None, description=None, is_public=None):
        kwargs = {"playlist_id": playlist_id, "user_id": user_id}
        if title is not None:
            kwargs["title"] = title
        if description is not None:
            kwargs["description"] = description
        if is_public is not None:
            kwargs["is_public"] = is_public
        req = playlist_pb2.UpdatePlaylistRequest(**kwargs)
        return self.stub.UpdatePlaylist(req)

    def delete_playlist(self, playlist_id: int, user_id: int):
        req = playlist_pb2.DeletePlaylistRequest(playlist_id=playlist_id, user_id=user_id)
        return self.stub.DeletePlaylist(req)

    def add_track(self, playlist_id: int, user_id: int, spotify_track_id: str, position: int):
        req = playlist_pb2.AddTrackRequest(
            playlist_id=playlist_id, user_id=user_id,
            spotify_track_id=spotify_track_id, position=position,
        )
        return self.stub.AddTrack(req)

    def remove_track(self, playlist_id: int, user_id: int, spotify_track_id: str):
        req = playlist_pb2.RemoveTrackRequest(
            playlist_id=playlist_id, user_id=user_id, spotify_track_id=spotify_track_id,
        )
        return self.stub.RemoveTrack(req)

    def list_user_playlists(self, user_id: int, request_user_id: int):
        req = playlist_pb2.ListUserPlaylistsRequest(user_id=user_id, request_user_id=request_user_id)
        return self.stub.ListUserPlaylists(req)