from typing import TypedDict, List

class AgentState(TypedDict):
    question: str
    subtasks: List[str]
    worker_outputs: List[str]
    draft_answer: str
    critique: str
    final_answer: str
    iteration: int