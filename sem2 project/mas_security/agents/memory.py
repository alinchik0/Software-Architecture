from pathlib import Path
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings


def init_rag():
	knowledge_dir = Path(__file__).resolve().parent.parent / "knowledge"
	if not knowledge_dir.is_dir():
		print("⚠️ Knowledge directory not found. RAG disabled.")
		return None

	loader = DirectoryLoader(str(knowledge_dir), glob="*.md", loader_cls=TextLoader,
	                         loader_kwargs={"autodetect_encoding": True})
	docs = loader.load()
	chunks = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50).split_documents(docs)
	emb = OllamaEmbeddings(model="nomic-embed-text")
	return Chroma.from_documents(chunks, emb, persist_directory="./chroma_db").as_retriever(k=2)


def log_memory(state: dict, agent: str, output: str) -> dict:
	state["memory_log"].append({
		"agent": agent,
		"output_preview": output[:100],
		"step": len(state["memory_log"])
	})
	return state