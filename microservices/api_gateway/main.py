# api_gateway/main.py
import sys
import os

# ==========================================
# OPENTELEMETRY IMPORTS (Добавлено для Observability)
# ==========================================
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(__file__))

import logging
import grpc
import asyncpg
import redis.asyncio as aioredis
from fastapi import FastAPI
from contextlib import asynccontextmanager

from config import GatewaySettings
from api_gateway.routers import auth
from shared.redis_cache import close as close_redis
from api_gateway.routers.playlists import router as playlists_router, user_playlists_router
from api_gateway.routers.catalog import router as catalog_router

from user_service.protos.generated import user_pb2, user_pb2_grpc
from playlist_service.protos.generated import playlist_pb2, playlist_pb2_grpc

# ==========================================
# OPENTELEMETRY INITIALIZATION
# ==========================================
# 1. Определяем имя сервиса
resource = Resource.create({"service.name": "api-gateway"})

# 2. Настраиваем экспорт трейсов в Jaeger (через OTel Collector)
trace.set_tracer_provider(TracerProvider(resource=resource))
otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://microservices-monitoring-otel-collector:4317")
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
)

# 3. Настраиваем экспорт метрик в Prometheus (через OTel Collector)
metric_reader = PeriodicExportingMetricReader(
    OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True),
    export_interval_millis=10000  # Отправка каждые 10 секунд
)
metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

# 4. Создаем объекты meter и tracer для использования в коде
meter = metrics.get_meter("api-gateway-meter")
tracer = trace.get_tracer("api-gateway-tracer")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gateway")
cfg = GatewaySettings()

# ==========================================
# КАСТОМНЫЕ МЕТРИКИ (3-4 штуки для выполнения задания)
# ==========================================
# Метрика 1: Счётчик всех запросов
req_counter = meter.create_counter("api_requests_total", description="Total API requests", unit="1")

# Метрика 2: Гистограмма времени ответа
req_latency = meter.create_histogram("api_request_duration_seconds", description="Request latency", unit="s")

# Метрика 3: Счётчик ошибок
error_counter = meter.create_counter("api_errors_total", description="Total API errors", unit="1")


def _to_asyncpg_url(url: str) -> str:
	return url.replace("postgresql+asyncpg://", "postgresql://")


@asynccontextmanager
async def lifespan(app: FastAPI):
	# === Startup ===
	log.info("Starting api-gateway...")

	# PostgreSQL (через asyncpg — нужен обычный URL)
	try:
		conn = await asyncpg.connect(_to_asyncpg_url(cfg.DATABASE_URL))
		await conn.fetchval("SELECT 1")
		await conn.close()
		log.info("Connected to PostgreSQL")
	except Exception as e:
		log.error(f"PostgreSQL connection failed: {e}")

	# Redis
	try:
		r = aioredis.from_url(cfg.REDIS_URL)
		await r.ping()
		await r.close()
		log.info("Connected to Redis")
	except Exception as e:
		log.error(f"Redis connection failed: {e}")

	yield

	# === Shutdown ===
	log.info("Shutting down api-gateway...")
	await close_redis()
	log.info("Api-gateway shutdown complete")


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(playlists_router)
app.include_router(user_playlists_router)
app.include_router(catalog_router)
# Эта одна строка автоматически добавит трейсы и метрики (http.server.duration) ко всем роутам
FastAPIInstrumentor.instrument_app(app)


@app.get("/health")
def health():
	req_counter.add(1, {"endpoint": "/health", "method": "GET", "status": "200"}) # <-- ДОБАВИТЬ ЭТУ СТРОКУ
	return {"status": "ok", "service": "api-gateway"}

def _grpc_ping(url, stub_cls, req):
    # Создаём кастомный span для трейса в Jaeger
    with tracer.start_as_current_span(f"grpc_ping_{url}") as span:
        ch = grpc.insecure_channel(url)
        try:
            resp = stub_cls(ch).Ping(req, timeout=2)
            req_counter.add(1, {"endpoint": f"/ping/{url.split(':')[0]}", "method": "GET", "status": "200"})
            return {"message": resp.message}
        except Exception as e:
            log.error(f"gRPC ping failed: {e}")
            error_counter.add(1, {"error_type": "grpc_call", "service": url}) # <-- Считаем ошибку
            span.set_status(trace.StatusCode.ERROR, str(e)) # <-- Помечаем трейс как ошибочный в Jaeger
            return {"error": str(e)}
        finally:
            ch.close()


@app.get("/ping/user")
def ping_user():
	return _grpc_ping(cfg.USER_GRPC_URL, user_pb2_grpc.UserServiceStub, user_pb2.PingRequest())


@app.get("/ping/playlist")
def ping_playlist():
	return _grpc_ping(cfg.PLAYLIST_GRPC_URL, playlist_pb2_grpc.PlaylistServiceStub, playlist_pb2.PingRequest())



from fastapi.staticfiles import StaticFiles
import os

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/app", StaticFiles(directory=static_dir, html=True), name="static")