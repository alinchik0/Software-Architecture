# user-service/repositories.py
import uuid
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models import User

class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def by_email_or_username(self, value: str) -> User | None:
        return (await self.session.execute(select(User).where(or_(User.email == value, User.username == value)))).scalar_one_or_none()

    async def by_id(self, user_id: str) -> User | None:
        return await self.session.get(User, uuid.UUID(user_id))

    async def create(self, email: str, username: str, password_hash: str) -> User:
        user = User(email=email, username=username, password_hash=password_hash)
        self.session.add(user)
        await self.session.flush()
        return user
