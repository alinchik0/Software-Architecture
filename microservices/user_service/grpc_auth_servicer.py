# user_service/grpc_auth_servicer.py
import grpc
from user_service.protos.generated import auth_pb2, auth_pb2_grpc
from user_service.auth_service import AuthService

class AuthServicer(auth_pb2_grpc.AuthServiceServicer):
    async def Register(self, request: auth_pb2.RegisterRequest, context) -> auth_pb2.RegisterResponse:
        """gRPC обработчик регистрации."""
        result = await AuthService.register_user(request.email, request.password)
        return auth_pb2.RegisterResponse(
            success=result["success"],
            message=result["message"],
            user_id=result["user_id"] or 0
        )

    async def Login(self, request: auth_pb2.LoginRequest, context) -> auth_pb2.LoginResponse:
        """gRPC обработчик логина."""
        result = await AuthService.login_user(request.email, request.password)
        return auth_pb2.LoginResponse(
            success=result["success"],
            message=result["message"],
            access_token=result["access_token"] or "",
            user_id=result["user_id"] or 0
        )

    async def Logout(self, request: auth_pb2.LogoutRequest, context) -> auth_pb2.LogoutResponse:
        """gRPC обработчик logout."""
        result = await AuthService.logout_user(request.token)
        return auth_pb2.LogoutResponse(
            success=result["success"],
            message=result["message"]
        )