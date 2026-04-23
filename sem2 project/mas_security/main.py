from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from agents.graph import graph, memory

app = FastAPI(title="MAS Security Doc Service", version="2.1")


class Query(BaseModel):
    question: str = Field(..., min_length=3)
    top_k: int = Field(5, ge=1, le=12)
    response_language: Literal["english", "russian"] = "english"


class IngestRequest(BaseModel):
    paths: List[str]


@app.post("/ingest")
def ingest(req: IngestRequest):
    added = memory.ingest_files(req.paths)
    return {"indexed_chunks": added, "indexed_files": len(req.paths)}


@app.post("/ingest/upload")
async def ingest_upload(files: List[UploadFile] = File(...)):
    temp_paths: List[str] = []
    try:
        for f in files:
            suffix = Path(f.filename).suffix.lower()
            if suffix not in {".md", ".txt", ".pdf"}:
                continue
            with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(await f.read())
                temp_paths.append(tmp.name)

        if not temp_paths:
            raise HTTPException(status_code=400, detail="No supported files (.md/.txt/.pdf)")

        added = memory.ingest_files(temp_paths)
        return {"indexed_chunks": added, "uploaded_files": len(temp_paths)}
    finally:
        for p in temp_paths:
            Path(p).unlink(missing_ok=True)


@app.post("/ask")
def ask(q: Query):
    state = {
        "question": q.question,
        "mode": "qa",
        "response_language": q.response_language,
        "top_k": q.top_k,
        "subtasks": [],
        "retrieved_chunks": [],
        "worker_outputs": [],
        "draft_answer": "",
        "critique": "",
        "final_answer": "",
        "iteration": 0,
    }

    result = graph.invoke(state)
    return {
        "mode": result.get("mode", "qa"),
        "response_language": result.get("response_language", q.response_language),
        "answer": result["final_answer"],
        "subtasks": result.get("subtasks", []),
    }
