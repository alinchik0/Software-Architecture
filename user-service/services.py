# user-service/services.py
import json
from dataclasses import dataclass
from grpc import StatusCode
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from shared.config import get_settings
from shared.events import KafkaProducer, build_event
from shared.security import create_token, decode_token, hash_password, verify_password
from repositories import UserRepository
from schemas import LoginIn, ProfileUpdate, RegisterIn

class ServiceError(Exception):
    def __init__(self, code: StatusCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

@dataclass(frozen=True)
class Tokens:
    access_token: str
    refresh_token: str

class UserServiceLogic:
    def __init__(self, session: AsyncSession, producer: KafkaProducer | None = None) -> None:
        self.session = session
        self.repo = UserRepository(session)
        self.producer = producer

    def _tokens(self, user_id: str) -> Tokens:
        s = get_settings()
        return Tokens(create_token(user_id, "access", s.access_token_ttl_seconds), create_token(user_id, "refresh", s.refresh_token_ttl_seconds))

    async def register(self, data: RegisterIn) -> tuple[str, Tokens]:
        if await self.repo.by_email_or_username(data.email) or await self.repo.by_email_or_username(data.username):
            raise ServiceError(StatusCode.ALREADY_EXISTS, "email or username already exists")
        user = await self.repo.create(data.email, data.username, hash_password(data.password))
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ServiceError(StatusCode.ALREADY_EXISTS, "email or username already exists") from exc
        if self.producer:
            event = build_event("user.registered", str(user.id), {"user_id": str(user.id), "email": user.email, "username": user.username})
            await self.producer.publish("user.events", str(user.id), event)
        return str(user.id), self._tokens(str(user.id))

    async def login(self, data: LoginIn) -> tuple[str, Tokens]:
        user = await self.repo.by_email_or_username(data.login)
        if not user or not verify_password(data.password, user.password_hash):
            raise ServiceError(StatusCode.UNAUTHENTICATED, "invalid credentials")
        return str(user.id), self._tokens(str(user.id))

    async def refresh(self, refresh_token: str) -> str:
        payload = decode_token(refresh_token)
        if payload.get("typ") != "refresh":
            raise ServiceError(StatusCode.UNAUTHENTICATED, "invalid refresh token")
        return create_token(str(payload["sub"]), "access", get_settings().access_token_ttl_seconds)

    async def profile(self, user_id: str):
        user = await self.repo.by_id(user_id)
        if not user:
            raise ServiceError(StatusCode.NOT_FOUND, "user not found")
        return user

    async def update_profile(self, user_id: str, data: ProfileUpdate):
        user = await self.profile(user_id)
        if data.username:
            user.username = data.username
        if data.profile_data is not None:
            user.profile_data = data.profile_data
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ServiceError(StatusCode.ALREADY_EXISTS, "username already exists") from exc
        await self.session.refresh(user)
        if self.producer:
            event = build_event("user.profile.updated", str(user.id), {"user_id": str(user.id), "profile_data": user.profile_data})
            await self.producer.publish("user.events", str(user.id), event)
        return user

def profile_json(user) -> str:
    return json.dumps(user.profile_data or {})
