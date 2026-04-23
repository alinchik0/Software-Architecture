import json
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from agents.state import AgentState
from agents.prompts import *

llm_small = ChatOllama(model="qwen2.5:3b", temperature=0.3, format="json")
llm_strong = ChatOllama(model="qwen2.5:7b", temperature=0.2, format="json")


def safe_json(text: str):
    try:
        return json.loads(text)
    except:
        return {}


# --- Planner ---
def planner_node(state: AgentState):
    prompt = f"{PLANNER_PROMPT}\nQuestion: {state['question']}"
    result = safe_json(llm_small.invoke(prompt).content)
    state["subtasks"] = result.get("subtasks", [])
    return state


# --- Workers ---
def worker_node(state: AgentState):
    outputs = []
    for task in state["subtasks"]:
        prompt = f"{WORKER_PROMPT}\nTask: {task}"
        resp = llm_small.invoke(prompt).content
        outputs.append(resp)
    state["worker_outputs"] = outputs
    return state


# --- Aggregator ---
def aggregator_node(state: AgentState):
    combined = "\n".join(state["worker_outputs"])
    prompt = f"{AGGREGATOR_PROMPT}\n{combined}"
    state["draft_answer"] = llm_small.invoke(prompt).content
    return state


# --- Critic ---
def critic_node(state: AgentState):
    prompt = f"{CRITIC_PROMPT}\nAnswer:\n{state['draft_answer']}"
    state["critique"] = llm_small.invoke(prompt).content
    return state


# --- Refiner ---
def refiner_node(state: AgentState):
    prompt = f"{REFINER_PROMPT}\nAnswer:\n{state['draft_answer']}\nIssues:\n{state['critique']}"
    state["draft_answer"] = llm_small.invoke(prompt).content
    return state


# --- Judge ---
def judge_node(state: AgentState):
    prompt = f"{JUDGE_PROMPT}\nAnswer:\n{state['draft_answer']}"
    result = safe_json(llm_strong.invoke(prompt).content)

    if result.get("verdict") == "accept" or state["iteration"] >= 2:
        state["final_answer"] = state["draft_answer"]
        return state

    state["iteration"] += 1
    return state


# --- Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("worker", worker_node)
workflow.add_node("aggregator", aggregator_node)
workflow.add_node("critic", critic_node)
workflow.add_node("refiner", refiner_node)
workflow.add_node("judge", judge_node)

workflow.set_entry_point("planner")

workflow.add_edge("planner", "worker")
workflow.add_edge("worker", "aggregator")
workflow.add_edge("aggregator", "critic")
workflow.add_edge("critic", "refiner")
workflow.add_edge("refiner", "judge")


def route(state):
    if state.get("final_answer"):
        return "end"
    return "critic"


workflow.add_conditional_edges(
    "judge",
    route,
    {
        "end": END,
        "critic": "critic"
    }
)

graph = workflow.compile()