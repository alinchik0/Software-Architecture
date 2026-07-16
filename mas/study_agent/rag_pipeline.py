# study_agent/rag_pipeline.py
import logging
import json
import time
from pathlib import Path
from study_agent.memory import collection
from study_agent.retriever import search_material
from shared.observability import get_tracer, get_meter
from shared.llm_client import call_llm, call_llm_json, HF_MODEL

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)
meter = get_meter(__name__)

# 📊 Метрики для RAG-пайплайна
rag_counter = meter.create_counter("rag_pipeline_executions")
rag_latency = meter.create_histogram("rag_pipeline_duration_seconds", unit="s")
rag_retrieval_chunks = meter.create_histogram("rag_retrieved_chunks_count", unit="chunks")

PROMPTS_DIR = Path(__file__).parent / "prompts"

def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")

def _retrieve_context(query: str, k: int = 5) -> list:
    chunks = search_material(query, k=k)
    rag_retrieval_chunks.record(len(chunks), attributes={"query_preview": query[:50]})
    return chunks

def _generate_draft(query: str, context: list) -> str:
    if not context:
        return "Insufficient data in materials to answer this question."

    context_text = "\n\n---\n\n".join([
        f"[Topic: {c['topic']}]\n{c['content']}"
        for c in context
    ])

    system_prompt = _load_prompt("qa_generation")
    user_prompt = f"Question: {query}\n\nContext:\n{context_text}"

    try:
        with tracer.start_as_current_span("rag.generation") as span:
            span.set_attributes({
                "gen_ai.operation.name": "generate",
                "gen_ai.request.model": HF_MODEL,
                "context_chunks": len(context)
            })

            # 🔄 ЗАМЕНА: используем call_llm вместо requests.post
            draft = call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,
                timeout=90
            )

            span.set_attributes({
                "gen_ai.response.finish_reason": "stop",
                "output.length": len(draft)
            })
            return draft if draft and not draft.startswith("Error:") else "Error generating answer."

    except Exception as e:
        logger.error("rag_generation_failed", extra={"error": str(e)})
        return "Error generating answer."

def _verify_and_cite(query: str, draft: str, context: list, attempt: int = 1, max_attempts: int = 2) -> dict:
    if not context or draft.startswith("Insufficient data") or draft.startswith("Error"):
        return {"answer": draft, "sources": []}

    context_text = "\n\n---\n\n".join([
        f"ID: {c['id']}, Topic: {c['topic']}\n{c['content']}"
        for c in context
    ])

    system_prompt = _load_prompt("qa_verification")
    user_prompt = f"""Question: {query}
Draft Answer: {draft}
Context: {context_text}
Return EXACTLY this JSON: {{"pass": true/false, "feedback": "...", "used_chunk_ids": ["..."]}}"""

    try:
        with tracer.start_as_current_span("rag.verification") as span:
            span.set_attributes({
                "gen_ai.operation.name": "verify",
                "gen_ai.request.model": HF_MODEL,
                "attempt": attempt
            })

            # 🔄 ЗАМЕНА: используем call_llm_json для гарантированного парсинга
            result = call_llm_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                timeout=60
            )

            if "error" in result:
                raise Exception(result["error"])

            if result.get("pass"):
                sources = [{"topic": c["topic"], "chunk_id": c["id"]}
                           for c in context if c["id"] in result.get("used_chunk_ids", [])]
                span.set_attributes({
                    "verification.passed": True,
                    "sources_count": len(sources)
                })
                return {"answer": draft, "sources": sources}

            # Регенерация при неудаче
            if attempt < max_attempts:
                new_draft = _generate_draft_with_feedback(query, context, result.get("feedback", ""))
                return _verify_and_cite(query, new_draft, context, attempt + 1, max_attempts)

            # Фолбэк
            span.set_attribute("verification.passed", False)
            sources = [{"topic": c["topic"], "chunk_id": c["id"]} for c in context[:2]]
            return {
                "answer": "Could not verify answer against materials. Here are relevant topics for manual review.",
                "sources": sources
            }

    except Exception as e:
        logger.error("rag_verification_failed", extra={"error": str(e)})
        sources = [{"topic": c["topic"], "chunk_id": c["id"]} for c in context[:2]]
        return {"answer": draft, "sources": sources}

def _generate_draft_with_feedback(query: str, context: list, feedback: str) -> str:
    context_text = "\n\n---\n\n".join([f"[Topic: {c['topic']}]\n{c['content']}" for c in context])
    system_prompt = _load_prompt("qa_generation_with_feedback")
    user_prompt = f"Question: {query}\nContext: {context_text}\nFeedback: {feedback}\nAnswer:"

    try:
        # 🔄 ЗАМЕНА: используем call_llm
        return call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            timeout=60
        )
    except Exception as e:
        logger.error("rag_regeneration_failed", extra={"error": str(e)})
        return "Error regenerating answer."

def answer_with_rag(query: str) -> dict:
    start_time = time.time()

    with tracer.start_as_current_span("rag_pipeline") as span:
        span.set_attributes({
            "gen_ai.operation.name": "rag_qa",
            "user_query": query[:200],
            "agent.type": "study"
        })
        rag_counter.add(1, attributes={"operation": "started"})

        try:
            context = _retrieve_context(query, k=5)
            if not context:
                rag_counter.add(1, attributes={"operation": "completed", "status": "no_context"})
                return {"answer": "No relevant materials found in the database.", "sources": []}

            draft = _generate_draft(query, context)
            # Для скорости пока делаем max_attempts=1. Если нужно строже, поставь 2.
            result = _verify_and_cite(query, draft, context, attempt=1, max_attempts=1)

            rag_counter.add(1, attributes={"operation": "completed", "status": "success",
                                           "sources": len(result["sources"])})
            return result

        except Exception as e:
            rag_counter.add(1, attributes={"operation": "completed", "status": "error", "error": type(e).__name__})
            span.record_exception(e)
            raise

        finally:
            rag_latency.record(time.time() - start_time, attributes={"operation": "answer_with_rag"})