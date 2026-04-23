from fastapi import FastAPI
from pydantic import BaseModel
from agents.graph import graph

app = FastAPI()


class Query(BaseModel):
    question: str


@app.post("/ask")
def ask(q: Query):
    state = {
        "question": q.question,
        "subtasks": [],
        "worker_outputs": [],
        "draft_answer": "",
        "critique": "",
        "final_answer": "",
        "iteration": 0
    }

    result = graph.invoke(state)
    return {"answer": result["final_answer"]}