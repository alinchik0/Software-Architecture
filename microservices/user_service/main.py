# user_service/main.py
import sys
import os
import asyncio
import logging
import grpc
from concurrent import futures
from sqlalchemy import text

# 🔧 Настраиваем пути для импортов
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from config import UserServiceSettings
from shared.database import engine
from shared.models.user import Base
from shared.redis_cache import redis_client, close as close_redis

# Импортируем сгенерированные protobuf файлы
from user_service.protos.generated import user_pb2, user_pb2_grpc, auth_pb2_grpc
from user_service.grpc_auth_servicer import AuthServicer


# Предполагаем, что у вас уже есть UserServiceServicer для Ping
# Если нет, создайте минимальный для совместимости
class UserServiceServicer(user_pb2_grpc.UserServiceServicer):
	def Ping(self, request, context):
		return user_pb2.PingResponse(message="pong from user-service")


logging.basicConfig(level=logging.INFO)
log = logging.getLogger("user-service")
cfg = UserServiceSettings()


async def init_db():
	"""Инициализирует базу данных."""
	try:
		async with engine.begin() as conn:
			await conn.run_sync(Base.metadata.create_all)
		log.info("Database initialized")
	except Exception as e:
		log.error(f"Failed to initialize database: {e}")
		raise


async def health_check():
	"""Проверяет подключение к БД и Redis."""
	# Проверка PostgreSQL
	try:
		async with engine.connect() as conn:
			await conn.execute(text("SELECT 1"))  # ✅ Обернули в text()
		log.info("Connected to PostgreSQL")
	except Exception as e:
		log.error(f"PostgreSQL connection failed: {e}")
		raise

	# Проверка Redis
	try:
		await redis_client.ping()
		log.info("Connected to Redis")
	except Exception as e:
		log.error(f"Redis connection failed: {e}")
		raise


async def serve():
	"""Запускает gRPC сервер."""
	server = None
	try:
		await health_check()
		await init_db()

		server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))

		# Регистрируем сервисы
		user_pb2_grpc.add_UserServiceServicer_to_server(UserServiceServicer(), server)
		auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServicer(), server)

		listen_addr = f"[::]:{cfg.GRPC_PORT}"
		server.add_insecure_port(listen_addr)

		log.info(f"Starting user-service on {listen_addr}")
		await server.start()

		# Graceful shutdown handler
		async def shutdown_handler():
			log.info("Received shutdown signal")
			if server:
				await server.stop(grace=5)
			await close_redis()
			await engine.dispose()
			log.info("User-service shutdown complete")

		# Регистрируем обработчик сигналов
		loop = asyncio.get_event_loop()
		for sig in (None,):  # Можно добавить signal.SIGINT, signal.SIGTERM
			pass  # В production добавьте обработку сигналов

		await server.wait_for_termination()

	except KeyboardInterrupt:
		log.info("Received keyboard interrupt")
	except Exception as e:
		log.error(f"Server error: {e}")
		raise
	finally:
		# Graceful shutdown
		log.info("Performing graceful shutdown...")
		if server:
			await server.stop(grace=5)
		await close_redis()
		await engine.dispose()
		log.info("Shutdown complete")


if __name__ == "__main__":
	try:
		asyncio.run(serve())
	except KeyboardInterrupt:
		log.info("Service stopped by user")
	except Exception as e:
		log.error(f"Fatal error: {e}")
		sys.exit(1)