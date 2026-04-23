from typing import List, TypedDict


class AgentState(TypedDict):
    question: str
    mode: str
    response_language: str
    top_k: int
    subtasks: List[str]
    retrieved_chunks: List[str]
    worker_outputs: List[str]
    draft_answer: str
    critique: str
    final_answer: str
    iteration: int
