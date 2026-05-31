# user-service/main.py
import asyncio
import json
import logging
from concurrent import futures
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db import get_session, SessionLocal
from shared.events import KafkaProducer
from shared.grpc_compile import compile_protos
from schemas import LoginIn, ProfileUpdate, RegisterIn
from services import ServiceError, UserServiceLogic, profile_json

compile_protos()
import grpc
import user_pb2
import user_pb2_grpc

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","message":"%(message)s"}')
app = FastAPI(title="user-service")

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/register")
async def register(data: RegisterIn, session: AsyncSession = Depends(get_session)):
    user_id, tokens = await UserServiceLogic(session, KafkaProducer()).register(data)
    return {"user_id": user_id, "tokens": tokens.__dict__}

class UserGrpc(user_pb2_grpc.UserServiceServicer):
    async def _logic(self) -> UserServiceLogic:
        return UserServiceLogic(SessionLocal(), KafkaProducer())

    async def Register(self, request, context):
        async with SessionLocal() as session:
            try:
                user_id, tokens = await UserServiceLogic(session, KafkaProducer()).register(RegisterIn(email=request.email, username=request.username, password=request.password))
                return user_pb2.AuthReply(user_id=user_id, tokens=user_pb2.TokenPair(access_token=tokens.access_token, refresh_token=tokens.refresh_token))
            except ServiceError as exc:
                await context.abort(exc.code, exc.message)

    async def Login(self, request, context):
        async with SessionLocal() as session:
            try:
                user_id, tokens = await UserServiceLogic(session).login(LoginIn(login=request.login, password=request.password))
                return user_pb2.AuthReply(user_id=user_id, tokens=user_pb2.TokenPair(access_token=tokens.access_token, refresh_token=tokens.refresh_token))
            except ServiceError as exc:
                await context.abort(exc.code, exc.message)

    async def Refresh(self, request, context):
        async with SessionLocal() as session:
            try:
                token = await UserServiceLogic(session).refresh(request.refresh_token)
                return user_pb2.TokenReply(access_token=token)
            except Exception:
                await context.abort(grpc.StatusCode.UNAUTHENTICATED, "invalid refresh token")

    async def GetProfile(self, request, context):
        async with SessionLocal() as session:
            try:
                user = await UserServiceLogic(session).profile(request.user_id)
                return user_pb2.ProfileReply(id=str(user.id), email=user.email, username=user.username, profile_data_json=profile_json(user), created_at=str(user.created_at), updated_at=str(user.updated_at))
            except ServiceError as exc:
                await context.abort(exc.code, exc.message)

    async def UpdateProfile(self, request, context):
        async with SessionLocal() as session:
            try:
                profile_data = json.loads(request.profile_data_json) if request.profile_data_json else None
                user = await UserServiceLogic(session, KafkaProducer()).update_profile(request.user_id, ProfileUpdate(username=request.username or None, profile_data=profile_data))
                return user_pb2.ProfileReply(id=str(user.id), email=user.email, username=user.username, profile_data_json=profile_json(user), created_at=str(user.created_at), updated_at=str(user.updated_at))
            except ServiceError as exc:
                await context.abort(exc.code, exc.message)

async def serve_grpc() -> None:
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    user_pb2_grpc.add_UserServiceServicer_to_server(UserGrpc(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    await server.wait_for_termination()

async def main() -> None:
    import uvicorn
    grpc_task = asyncio.create_task(serve_grpc())
    config = uvicorn.Config(app, host="0.0.0.0", port=8001, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
    grpc_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
