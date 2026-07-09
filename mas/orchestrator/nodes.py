# orchestrator/nodes.py
import logging
import os
import requests

from shared.observability import get_tracer

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)  # Для событий, не для новых спанов

# from notes_agent.agent import handle_request as notes_agent
# from study_agent.agent import handle_request as study_agent

NOTES_URL = os.getenv("NOTES_AGENT_URL", "http://localhost:8001")
STUDY_URL = os.getenv("STUDY_AGENT_URL", "http://localhost:8002")


def notes_node(state):
    # with tracer.start_as_current_span("notes_agent_call") as span:
    #     span.set_attribute("agent.type", "notes")
    #     logger.info("notes_node_executed", extra={"input_preview": str(state["input"])[:100]})
    #     result = notes_agent(state["input"])
    #     return {"output": str(result)}
    with tracer.start_as_current_span("notes_node_http") as span:
        print("got here")
        span.set_attribute("target_service", NOTES_URL)
        try:
            resp = requests.post(f"{NOTES_URL}/execute", json={"input": state["input"]}, timeout=30)
            resp.raise_for_status()
            return {"output": resp.json()["result"]}
        except Exception as e:
            span.record_exception(e)
            return {"output": f"Notes Agent Error: {str(e)}"}


def study_node(state):
    # with tracer.start_as_current_span("study_agent_call") as span:
    #     span.set_attribute("agent.type", "study")
    #     logger.info("study_node_executed", extra={"input_preview": str(state["input"])[:100]})
    #     result = study_agent(state["input"])
    #     return {"output": str(result)}

    with tracer.start_as_current_span("study_node_http") as span:
        print("got here")
        span.set_attribute("target_service", STUDY_URL)
        try:
            resp = requests.post(f"{STUDY_URL}/execute", json={"input": state["input"]}, timeout=30)
            resp.raise_for_status()
            return {"output": resp.json()["result"]}
        except Exception as e:
            span.record_exception(e)
            return {"output": f"Study Agent Error: {str(e)}"}