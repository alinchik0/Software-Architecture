# api_gateway/grpc_client.py
import grpc
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

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