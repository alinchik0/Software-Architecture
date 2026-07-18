# shared/observability.py
import os
import logging
import atexit
from opentelemetry import trace

try:
	from langfuse import Langfuse
except ImportError:
	Langfuse = None

logger = logging.getLogger(__name__)

langfuse_client = None
_otel_initialized = False


def setup_observability(service_name: str):
	"""Инициализирует Langfuse (который под капотом настроит OpenTelemetry)."""
	global langfuse_client, _otel_initialized
	if _otel_initialized:
		return

	public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
	secret_key = os.getenv("LANGFUSE_SECRET_KEY")
	host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com").rstrip("/")

	if not public_key or not secret_key:
		logger.warning("⚠️ [Observability] LANGFUSE_PUBLIC_KEY или LANGFUSE_SECRET_KEY не найдены в .env.")
		return

	if Langfuse is None:
		logger.error("❌ [Observability] Библиотека 'langfuse' не установлена. Выполните: pip install langfuse")
		return

	try:
		# Инициализируем родной клиент Langfuse.
		# Теперь он корректно прочитает HTTP_PROXY / ALL_PROXY из системы
		# и использует твой VPN благодаря установленному httpx[socks]
		langfuse_client = Langfuse(
			public_key=public_key,
			secret_key=secret_key,
			host=host,
			release=service_name,
			debug=True  # Поставь True, если хочешь видеть детальные логи отправки
		)

		_otel_initialized = True
		logger.info(f"✅ [Observability] Langfuse успешно инициализирован для '{service_name}' (через прокси).")

	except Exception as e:
		logger.error(f"❌ [Observability] Ошибка инициализации Langfuse: {e}")


def get_tracer(name: str):
	"""Возвращает стандартный OpenTelemetry tracer (совместим с Langfuse)."""
	return trace.get_tracer(name)


def get_meter(name: str):
	"""Заглушка для метрик для совместимости с существующим кодом."""
	from opentelemetry import metrics
	return metrics.get_meter(name)


def flush_observability():
	"""Гарантированно отправляет все оставшиеся трейсы перед закрытием."""
	global langfuse_client
	if langfuse_client:
		logger.info("🔄 [Observability] Отправка остаточных данных в Langfuse...")
		try:
			langfuse_client.flush()
			logger.info("✅ [Observability] Отправка завершена.")
		except Exception as e:
			logger.error(f"❌ [Observability] Ошибка при отправке: {e}")


# Автоматический flush при завершении работы Python
atexit.register(flush_observability)