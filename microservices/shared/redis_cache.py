# shared/redis.py
import redis.asyncio as redis
from shared.config import SharedSettings
import logging

settings = SharedSettings()
log = logging.getLogger("redis")

# Асинхронный клиент Redis с настройками подключения
redis_client = redis.from_url(
	settings.REDIS_URL,
	decode_responses=True,
	socket_connect_timeout=5,
	socket_timeout=5,
	retry_on_timeout=True,
	health_check_interval=30,
	max_connections=50
)


async def add_to_blacklist(token: str, expire_seconds: int) -> None:
	"""
    Добавляет токен в blacklist с TTL.

    Args:
        token: JWT токен для добавления в blacklist
        expire_seconds: Время жизни токена в секундах (до его истечения)
    """
	try:
		if expire_seconds <= 0:
			log.warning(f"Token expire_seconds is {expire_seconds}, skipping blacklist")
			return

		await redis_client.setex(f"blacklist:{token}", expire_seconds, "true")
		log.info(f"Token added to blacklist with TTL {expire_seconds}s")
	except redis.RedisError as e:
		log.error(f"Failed to add token to blacklist: {e}")
		raise
	except Exception as e:
		log.error(f"Unexpected error adding token to blacklist: {e}")
		raise


async def is_token_blacklisted(token: str) -> bool:
	"""
    Проверяет, находится ли токен в blacklist.

    Args:
        token: JWT токен для проверки

    Returns:
        bool: True если токен в blacklist, False иначе
    """
	try:
		exists = await redis_client.exists(f"blacklist:{token}")
		return exists > 0
	except redis.RedisError as e:
		log.error(f"Failed to check token blacklist: {e}")
		# В случае ошибки Redis, считаем токен валидным (fail-open)
		# или можно вернуть True для fail-close (более безопасно)
		return False
	except Exception as e:
		log.error(f"Unexpected error checking token blacklist: {e}")
		return False


async def ping() -> bool:
	"""
    Проверяет подключение к Redis.

    Returns:
        bool: True если Redis доступен, False иначе
    """
	try:
		await redis_client.ping()
		return True
	except redis.RedisError as e:
		log.error(f"Redis ping failed: {e}")
		return False
	except Exception as e:
		log.error(f"Unexpected error during Redis ping: {e}")
		return False


async def close() -> None:
	"""
    Graceful shutdown Redis клиента.
    Закрывает все соединения и освобождает ресурсы.
    """
	try:
		await redis_client.close()
		log.info("Redis connection closed")
	except Exception as e:
		log.error(f"Error closing Redis connection: {e}")


async def health_check() -> dict:
	"""
    Выполняет health check Redis.

    Returns:
        dict: Информация о состоянии Redis
    """
	try:
		info = await redis_client.info()
		return {
			"status": "healthy",
			"connected_clients": info.get("connected_clients", 0),
			"used_memory_human": info.get("used_memory_human", "N/A"),
			"uptime_in_seconds": info.get("uptime_in_seconds", 0)
		}
	except Exception as e:
		log.error(f"Redis health check failed: {e}")
		return {
			"status": "unhealthy",
			"error": str(e)
		}