import time  # Исправлен импорт (было ошибочно from datetime import time)
from langgraph.graph import StateGraph, END
from orchestrator.state import GraphState
from orchestrator.router import route_request
from orchestrator.nodes import notes_node, study_node

from shared.observability import get_tracer, get_meter

# Инициализируем инструменты
tracer = get_tracer(__name__)
meter = get_meter(__name__)
request_counter = meter.create_counter("orchestrator_requests")

# 📊 Гистограмма задержек (обязательна для статистики в LangFuse/Prometheus)
latency_histogram = meter.create_histogram(
	"orchestrator_node_duration_seconds",
	description="Execution time per graph node",
	unit="s"
)


def router_node(state):
	with tracer.start_as_current_span("router") as span:
		start_time = time.time()
		try:
			# 🏷️ Семантические атрибуты для автоматического парсинга LangFuse UI
			span.set_attributes({
				"gen_ai.system": "ollama",
				"gen_ai.request.model": "qwen3.5:2b-q4_K_M",
				"orchestrator.stage": "routing",
				"input.preview": str(state.get("input", ""))[:100]  # Безопасный превью для трейса
			})

			request_counter.add(1, attributes={"stage": "routing"})
			route = route_request(state["input"])

			span.set_attribute("chosen_route", route)
			latency_histogram.record(time.time() - start_time, attributes={"node": "router"})
			return {"route": route}

		except Exception as e:
			span.record_exception(e)
			span.set_status({"status_code": "ERROR", "description": str(e)})
			# 📉 Фиксируем задержку даже при ошибке (важно для метрик p95/p99)
			latency_histogram.record(time.time() - start_time, attributes={"node": "router", "error": type(e).__name__})
			raise


def route_decision(state):
	return state["route"]


def build_graph():
	graph = StateGraph(GraphState)

	graph.add_node("router", router_node)
	graph.add_node("notes", notes_node)
	graph.add_node("study", study_node)

	graph.set_entry_point("router")

	graph.add_conditional_edges(
		"router",
		route_decision,
		{
			"notes": "notes",
			"study": "study"
		}
	)

	graph.add_edge("notes", END)
	graph.add_edge("study", END)

	return graph.compile()