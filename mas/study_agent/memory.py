import chromadb
from chromadb.config import Settings
from study_agent.embeddings import get_embedding
import uuid

from pathlib import Path


# db_path = Path(__file__).parent.parent / "chroma_db"
# client = chromadb.Client(Settings(persist_directory=str(db_path)))
#
# collection = client.get_or_create_collection(name="study_materials")

DATA_DIR = Path.home() / ".study_agent_data"
db_path = DATA_DIR / "chroma_db"
db_path.mkdir(parents=True, exist_ok=True)

client = chromadb.PersistentClient(path=str(db_path))
collection = client.get_or_create_collection(name="study_materials")

def add_material(topic: str, content: str):
    chunks = split_text(content)

    ids = []
    embeddings = []
    metadatas = []
    documents = []

    for chunk in chunks:
        ids.append(str(uuid.uuid4()))
        embeddings.append(get_embedding(chunk))
        metadatas.append({"topic": topic})
        documents.append(chunk)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        metadatas=metadatas,
        documents=documents
    )

    return f"Material '{topic}' added with {len(chunks)} chunks"


def get_material(topic: str):
    results = collection.get(where={"topic": topic})

    return "\n".join(results["documents"])


def delete_material(topic: str):
    results = collection.get(where={"topic": topic})

    if not results["ids"]:
        return "No material found"

    collection.delete(ids=results["ids"])

    return f"Deleted material: {topic}"


def split_text(text: str, chunk_size: int = 300):
    words = text.split()
    chunks = []

    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))

    return chunks