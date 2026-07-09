# study_agent/retriever.py
import logging
from study_agent.memory import collection
from study_agent.embeddings import get_embedding

logger = logging.getLogger(__name__)


def search_material(query: str, k: int = 5, similarity_threshold: float = 0.85) -> list:
    # Генерация эмбеддинга
    try:
        query_embedding = get_embedding(query)
    except Exception as e:
        logger.error("retriever_embedding_failed", extra={"error": str(e)})
        return []

    # Векторный поиск
    try:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        logger.error("retriever_query_failed", extra={"error": str(e)})
        return []

    if not results["documents"] or not results["documents"][0]:
        logger.debug("retriever_vector_empty", extra={"query_preview": query[:50]})
        return _keyword_search(query, k=k)

    # Фильтрация по расстоянию
    best_dist = min(results["distances"][0])
    valid_indices = [i for i, dist in enumerate(results["distances"][0]) if dist < similarity_threshold]

    if not valid_indices:
        logger.debug("retriever_below_threshold", extra={"best_distance": best_dist})
        return _keyword_search(query, k=k)

    return [
        {
            "id": results["ids"][0][i],
            "topic": results["metadatas"][0][i].get("topic", "unknown"),
            "content": results["documents"][0][i]
        }
        for i in valid_indices
    ]


def _keyword_search(query: str, k: int = 3) -> list:
    """Fallback: текстовый поиск, если векторный не сработал."""
    all_results = collection.get(include=["documents", "metadatas"])
    if not all_results["ids"]:
        return []

    query_words = set(query.lower().split())
    scored = []

    for doc, meta, doc_id in zip(all_results["documents"], all_results["metadatas"], all_results["ids"]):
        overlap = len(query_words & set(doc.lower().split()))
        if overlap > 0:
            scored.append({"id": doc_id, "topic": meta.get("topic", "unknown"), "content": doc, "score": overlap})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:k]