# shared/observability.py
import logging
import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import SimpleLogRecordProcessor

_otel_initialized = False
_meter_provider = None  # Глобальная ссылка для force_flush


def setup_observability(service_name: str):
    """Инициализировать OTel один раз для всего приложения."""
    global _otel_initialized, _meter_provider
    if _otel_initialized:
        return

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    base_url = os.getenv("LANGFUSE_BASE_URL", "https://cloud.langfuse.com").rstrip("/")

    # LangFuse OTLP endpoint: {base_url}/api/public/otel
    endpoint = f"{base_url}/api/public/otel" if public_key and secret_key else None

    # LangFuse auth header: Bearer {public_key}:{secret_key}
    headers = {"Authorization": f"Bearer {public_key}:{secret_key}"} if public_key and secret_key else {}

    if not endpoint or not headers:
        print("⚠️ OTel env vars not set, skipping initialization")
        return

    resource = Resource.create({"service.name": service_name})

    # ===== TRACES =====
    trace_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(trace_provider)
    span_exporter = OTLPSpanExporter(endpoint=endpoint, headers=headers, timeout=10)
    trace_provider.add_span_processor(SimpleSpanProcessor(span_exporter))

    # ===== METRICS =====
    metric_exporter = OTLPMetricExporter(endpoint=endpoint, headers=headers, timeout=10)
    reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=10000)  # 10 сек для тестов
    _meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(_meter_provider)

    # ===== LOGS =====
    logger_provider = LoggerProvider(resource=resource)
    log_exporter = OTLPLogExporter(endpoint=endpoint, headers=headers, timeout=10)
    logger_provider.add_log_record_processor(SimpleLogRecordProcessor(log_exporter))

    otel_handler = LoggingHandler(logger_provider=logger_provider, level=logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if not any(isinstance(h, LoggingHandler) for h in root_logger.handlers):
        root_logger.addHandler(otel_handler)

    _otel_initialized = True
    print(f"✅ Observability initialized for {service_name}")


def get_tracer(name: str):
    return trace.get_tracer(name)


def get_meter(name: str):
    return metrics.get_meter(name)


def flush_observability():
    """Принудительно отправить все накопленные данные (для CLI-скриптов)."""
    if _otel_initialized:
        trace.get_tracer_provider().force_flush()
        if _meter_provider:
            _meter_provider.force_flush()