# api-gateway/grpc_clients/clients.py
from shared.config import get_settings
from shared.grpc_compile import compile_protos
compile_protos()
import grpc
import user_pb2_grpc
import playlist_pb2_grpc

def user_stub():
    s = get_settings()
    return user_pb2_grpc.UserServiceStub(grpc.aio.insecure_channel(f"{s.user_grpc_host}:{s.user_grpc_port}"))

def playlist_stub():
    s = get_settings()
    return playlist_pb2_grpc.PlaylistServiceStub(grpc.aio.insecure_channel(f"{s.playlist_grpc_host}:{s.playlist_grpc_port}"))
