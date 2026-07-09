# study_agent/tools.py
import logging
from study_agent.memory import add_material as db_add, get_material as db_get, delete_material as db_delete
from study_agent.rag_pipeline import answer_with_rag
from study_agent.retriever import search_material as db_search

logger = logging.getLogger(__name__)


def add_material(topic: str, content: str):
    logger.debug("tool.add_material", extra={"topic": topic})
    return db_add(topic, content)


def get_material(topic: str):
    logger.debug("tool.get_material", extra={"topic": topic})
    return db_get(topic)


def search_material(query: str):
    logger.debug("tool.search_material", extra={"query_preview": query[:50]})
    return db_search(query)


def delete_material(topic: str):
    logger.debug("tool.delete_material", extra={"topic": topic})
    return db_delete(topic)


def answer_question(query: str) -> dict:
    logger.info("tool.answer_question", extra={"query_preview": query[:100]})
    return answer_with_rag(query)