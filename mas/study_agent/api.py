from fastapi import FastAPI
from pydantic import BaseModel
from study_agent.agent import handle_request

app = FastAPI(title="Study Agent")

class Query(BaseModel):
    input: str

@app.post("/execute")
def execute(query: Query):
    return {"result": handle_request(query.input)}

@app.get("/health")
def health():
    return {"status": "ok"}