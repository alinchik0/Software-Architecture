import json
from typing import Any, Dict, List

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

from agents.memory import DocumentMemory
from agents.prompts import (
    AGGREGATOR_PROMPT,
    CRITIC_PROMPT,
    JUDGE_PROMPT,
    PLANNER_PROMPT,
    REFINER_PROMPT,
    RESEARCHER_PROMPT,
)
from agents.state import AgentState

# Разные модели на разных ролях (акцент на мультиагентность)
llm_planner = ChatOllama(model="qwen2.5:3b", temperature=0.1, format="json")
llm_researcher = ChatOllama(model="qwen2.5:7b", temperature=0.2)
llm_aggregator = ChatOllama(model="llama3.1:8b", temperature=0.2)
llm_critic = ChatOllama(model="qwen2.5:3b", temperature=0.1, format="json")
llm_judge = ChatOllama(model="qwen2.5:7b", temperature=0.0, format="json")

memory = DocumentMemory()
# Базовая индексация знаний проекта при запуске
memory.ingest_knowledge_folder()


def safe_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        return {}


def _compose_context(chunks: List[str]) -> str:
    if not chunks:
        return "CONTEXT: <empty>"
    clipped = chunks[:8]
    return "\n\n".join([f"[chunk {i + 1}] {c}" for i, c in enumerate(clipped)])


# --- Planner ---
def planner_node(state: AgentState):
    prompt = f"{PLANNER_PROMPT}\n\nQuestion: {state['question']}"
    result = safe_json(llm_planner.invoke(prompt).content)

    state["mode"] = result.get("mode", "qa")
    state["subtasks"] = result.get("subtasks", [state["question"]])
    return state


# --- Retrieval coordinator ---
def retrieval_node(state: AgentState):
    docs = memory.retrieve(state["question"], k=state.get("top_k", 5))
    state["retrieved_chunks"] = [d.page_content for d in docs]
    return state


# --- Research workers ---
def worker_node(state: AgentState):
    context = _compose_context(state.get("retrieved_chunks", []))
    outputs = []

    for task in state["subtasks"]:
        prompt = (
            f"{RESEARCHER_PROMPT}\n\n"
            f"MODE: {state['mode']}\n"
            f"RESPONSE_LANGUAGE: {state.get('response_language', 'english')}\n"
            f"SUBTASK: {task}\n\n"
            f"{context}"
        )
        resp = llm_researcher.invoke(prompt).content
        outputs.append(resp)

    state["worker_outputs"] = outputs
    return state


# --- Aggregator ---
def aggregator_node(state: AgentState):
    context = _compose_context(state.get("retrieved_chunks", []))
    combined = "\n\n".join(state.get("worker_outputs", []))
    prompt = (
        f"{AGGREGATOR_PROMPT}\n\n"
        f"MODE: {state['mode']}\n"
        f"RESPONSE_LANGUAGE: {state.get('response_language', 'english')}\n"
        f"QUESTION: {state['question']}\n\n"
        f"WORKER_OUTPUTS:\n{combined}\n\n"
        f"SOURCE_CONTEXT:\n{context}"
    )
    state["draft_answer"] = llm_aggregator.invoke(prompt).content
    return state


# --- Critic ---
def critic_node(state: AgentState):
    prompt = (
        f"{CRITIC_PROMPT}\n\n"
        f"QUESTION: {state['question']}\n"
        f"ANSWER:\n{state['draft_answer']}"
    )
    result = safe_json(llm_critic.invoke(prompt).content)
    state["critique"] = "\n".join(result.get("issues", []))
    return state


# --- Refiner ---
def refiner_node(state: AgentState):
    context = _compose_context(state.get("retrieved_chunks", []))
    prompt = (
        f"{REFINER_PROMPT}\n\n"
        f"QUESTION: {state['question']}\n"
        f"RESPONSE_LANGUAGE: {state.get('response_language', 'english')}\n"
        f"ISSUES:\n{state['critique']}\n\n"
        f"CURRENT_ANSWER:\n{state['draft_answer']}\n\n"
        f"SOURCE_CONTEXT:\n{context}"
    )
    state["draft_answer"] = llm_aggregator.invoke(prompt).content
    return state


# --- Judge ---
def judge_node(state: AgentState):
    prompt = f"{JUDGE_PROMPT}\n\nANSWER:\n{state['draft_answer']}"
    result = safe_json(llm_judge.invoke(prompt).content)

    if result.get("verdict") == "accept" or state["iteration"] >= 2:
        state["final_answer"] = state["draft_answer"]
        return state

    state["iteration"] += 1
    return state


workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("retrieval", retrieval_node)
workflow.add_node("worker", worker_node)
workflow.add_node("aggregator", aggregator_node)
workflow.add_node("critic", critic_node)
workflow.add_node("refiner", refiner_node)
workflow.add_node("judge", judge_node)

workflow.set_entry_point("planner")
workflow.add_edge("planner", "retrieval")
workflow.add_edge("retrieval", "worker")
workflow.add_edge("worker", "aggregator")
workflow.add_edge("aggregator", "critic")
workflow.add_edge("critic", "refiner")
workflow.add_edge("refiner", "judge")


def route(state: AgentState):
    return "end" if state.get("final_answer") else "critic"


workflow.add_conditional_edges("judge", route, {"end": END, "critic": "critic"})

graph = workflow.compile()
