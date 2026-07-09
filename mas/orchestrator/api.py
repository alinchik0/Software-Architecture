from fastapi import FastAPI
from pydantic import BaseModel
from orchestrator.graph import build_graph

app = FastAPI(title="Orchestrator")
graph = build_graph()

class UserInput(BaseModel):
    input: str

@app.post("/chat")
def chat(req: UserInput):
    result = graph.invoke({"input": req.input})
    return {"output": result["output"]}