import requests

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"


EMBED_MODEL = "nomic-embed-text"


def get_embedding(text: str):
    response = requests.post(OLLAMA_EMBED_URL, json={
        "model": EMBED_MODEL,
        "prompt": text
    })
    return response.json()["embedding"]