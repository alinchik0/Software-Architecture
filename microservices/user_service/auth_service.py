# user_service/auth_service.py
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from shared.models.user import User
from shared.security import get_password_hash, verify_password, create_access_token
from shared.database import async_session_factory
from shared.redis_cache import add_to_blacklist
from datetime import timedelta
from shared.config import SharedSettings

settings = SharedSettings()


class AuthService:
	@staticmethod
	async def register_user(email: str, password: str) -> dict:
		"""Регистрирует нового пользователя."""
		async with async_session_factory() as session:
			try:
				# Проверяем, существует ли пользователь
				existing_user = await session.execute(select(User).where(User.email == email))
				if existing_user.scalar_one_or_none():
					return {"success": False, "message": "Email already registered", "user_id": None}

				# Создаем нового пользователя
				hashed_password = get_password_hash(password)
				new_user = User(email=email, hashed_password=hashed_password)
				session.add(new_user)
				await session.commit()
				await session.refresh(new_user)

				return {"success": True, "message": "User registered successfully", "user_id": new_user.id}

			except IntegrityError:
				await session.rollback()
				return {"success": False, "message": "Email already registered", "user_id": None}
			except Exception as e:
				await session.rollback()
				return {"success": False, "message": f"Registration failed: {str(e)}", "user_id": None}

	@staticmethod
	async def login_user(email: str, password: str) -> dict:
		"""Аутентифицирует пользователя и возвращает JWT токен."""
		async with async_session_factory() as session:
			try:
				result = await session.execute(select(User).where(User.email == email))
				user = result.scalar_one_or_none()

				if not user or not verify_password(password, user.hashed_password):
					return {"success": False, "message": "Invalid credentials", "access_token": None, "user_id": None}

				# Создаем access token
				access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
				access_token = create_access_token(
					data={"sub": str(user.id), "email": user.email},
					expires_delta=access_token_expires
				)

				return {
					"success": True,
					"message": "Login successful",
					"access_token": access_token,
					"user_id": user.id
				}

			except Exception as e:
				return {"success": False, "message": f"Login failed: {str(e)}", "access_token": None, "user_id": None}

	@staticmethod
	async def logout_user(token: str) -> dict:
		"""Добавляет токен в blacklist при logout."""
		try:
			from shared.security import decode_access_token
			payload = decode_access_token(token)
			if not payload:
				return {"success": False, "message": "Invalid token"}

			# Вычисляем оставшееся время жизни токена
			exp = payload.get("exp")
			if not exp:
				return {"success": False, "message": "Token has no expiration"}

			from time import time
			remaining_time = int(exp - time())
			if remaining_time <= 0:
				return {"success": False, "message": "Token already expired"}

			# Добавляем в blacklist
			await add_to_blacklist(token, remaining_time)
			return {"success": True, "message": "Logged out successfully"}

		except Exception as e:
			return {"success": False, "message": f"Logout failed: {str(e)}"}