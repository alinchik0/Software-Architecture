# api-gateway/routes/auth.py
from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field
from auth.jwt import blacklist_token
from grpc_clients.clients import user_stub
import grpc
import user_pb2

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class RegisterBody(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    username: str = Field(min_length=3)
    password: str = Field(min_length=8)
class LoginBody(BaseModel):
    login: str
    password: str
class RefreshBody(BaseModel):
    refresh_token: str
class LogoutBody(BaseModel):
    access_token: str

def grpc_error(exc: grpc.aio.AioRpcError) -> HTTPException:
    mapping = {grpc.StatusCode.ALREADY_EXISTS: 409, grpc.StatusCode.UNAUTHENTICATED: 401, grpc.StatusCode.NOT_FOUND: 404, grpc.StatusCode.PERMISSION_DENIED: 403, grpc.StatusCode.INVALID_ARGUMENT: 400}
    return HTTPException(mapping.get(exc.code(), 500), exc.details())

@router.post("/register")
async def register(body: RegisterBody):
    try:
        r = await user_stub().Register(user_pb2.RegisterRequest(email=body.email, username=body.username, password=body.password))
        return {"user_id": r.user_id, "tokens": {"access_token": r.tokens.access_token, "refresh_token": r.tokens.refresh_token}}
    except grpc.aio.AioRpcError as exc:
        raise grpc_error(exc)

@router.post("/login")
async def login(body: LoginBody):
    try:
        r = await user_stub().Login(user_pb2.LoginRequest(login=body.login, password=body.password))
        return {"tokens": {"access_token": r.tokens.access_token, "refresh_token": r.tokens.refresh_token}}
    except grpc.aio.AioRpcError as exc:
        raise grpc_error(exc)

@router.post("/refresh")
async def refresh(body: RefreshBody):
    try:
        r = await user_stub().Refresh(user_pb2.RefreshRequest(refresh_token=body.refresh_token))
        return {"new_access_token": r.access_token}
    except grpc.aio.AioRpcError as exc:
        raise grpc_error(exc)

@router.post("/logout", status_code=204)
async def logout(body: LogoutBody):
    await blacklist_token(body.access_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
