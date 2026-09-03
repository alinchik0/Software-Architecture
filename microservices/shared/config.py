# shared/config.py
from pydantic_settings import BaseSettings
import os


class SharedSettings(BaseSettings):
	# ВАЖНО: для async SQLAlchemy нужен префикс postgresql+asyncpg
	DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/music_db"
	REDIS_URL: str = "redis://redis:6379"

	SECRET_KEY: str = "your-secret-key-change-in-production"
	ALGORITHM: str = "HS256"
	ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

	class Config:
		env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
		env_file_encoding = "utf-8"
		extra = "ignore"