from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentMemory:
    """Хранилище документов + retriever для RAG."""

    def __init__(self, persist_directory: str = "./chroma_db", embedding_model: str = "nomic-embed-text"):
        self.persist_directory = persist_directory
        self.embeddings = OllamaEmbeddings(model=embedding_model)
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=900, chunk_overlap=180)
        self.vectordb = Chroma(
            collection_name="docs_collection",
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
        )

    def _load_file(self, file_path: Path) -> List[Document]:
        suffix = file_path.suffix.lower()
        if suffix in {".md", ".txt"}:
            loader = TextLoader(str(file_path), autodetect_encoding=True)
            return loader.load()
        if suffix == ".pdf":
            loader = PyPDFLoader(str(file_path))
            return loader.load()
        return []

    def ingest_files(self, file_paths: Iterable[str]) -> int:
        loaded_docs: List[Document] = []
        for raw in file_paths:
            path = Path(raw).expanduser().resolve()
            if not path.exists() or not path.is_file():
                continue
            loaded_docs.extend(self._load_file(path))

        if not loaded_docs:
            return 0

        chunks = self.splitter.split_documents(loaded_docs)
        self.vectordb.add_documents(chunks)
        return len(chunks)

    def ingest_knowledge_folder(self, folder: Optional[str] = None) -> int:
        base = Path(folder).resolve() if folder else Path(__file__).resolve().parent.parent / "knowledge"
        if not base.exists():
            return 0

        files = [str(p) for p in base.glob("**/*") if p.suffix.lower() in {".md", ".txt", ".pdf"}]
        return self.ingest_files(files)

    def retrieve(self, query: str, k: int = 4) -> List[Document]:
        retriever = self.vectordb.as_retriever(search_kwargs={"k": k})
        return retriever.invoke(query)


def log_memory(state: dict, agent: str, output: str) -> dict:
    state.setdefault("memory_log", []).append(
        {
            "agent": agent,
            "output_preview": output[:160],
            "step": len(state.get("memory_log", [])),
        }
    )
    return state
