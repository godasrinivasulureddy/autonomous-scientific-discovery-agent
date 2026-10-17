
import os

from dotenv import load_dotenv
from google import genai
from pinecone import Pinecone

load_dotenv()

INDEX_NAME = "scientific-papers"
EMBEDDING_MODEL = "gemini-embedding-001"
DIMENSION = 768


def get_clients():
    """Connect to Gemini embeddings and Pinecone."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    pinecone_key = os.getenv("PINECONE_API_KEY")

    if not gemini_key or not pinecone_key:
        raise ValueError("GEMINI_API_KEY and PINECONE_API_KEY are required.")

    gemini_client = genai.Client(api_key=gemini_key)
    pinecone_client = Pinecone(api_key=pinecone_key)

    return gemini_client, pinecone_client.Index(INDEX_NAME)


def embed_text(text, task_type):
    """Generate a 768-dimensional Gemini embedding."""
    if not text or not text.strip():
        raise ValueError("Text cannot be empty.")

    gemini_client, _ = get_clients()

    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config={
            "task_type": task_type,
            "output_dimensionality": DIMENSION,
        },
    )

    return response.embeddings[0].values


def store_paper(paper_id, title, text, source, url=""):
    """Store a scientific paper in Pinecone."""
    if not paper_id or not title or not text or not text.strip():
        raise ValueError("Paper ID, title, and text are required.")

    vector = embed_text(text, "RETRIEVAL_DOCUMENT")
    _, index = get_clients()

    index.upsert(
        vectors=[
            {
                "id": str(paper_id),
                "values": vector,
                "metadata": {
                    "title": title,
                    "text": text,
                    "source": source,
                    "url": url,
                },
            }
        ]
    )

    return {"status": "stored", "paper_id": str(paper_id)}


def search_papers(query, top_k=3):
    """Find scientifically relevant papers using vector similarity."""
    if not query or not query.strip():
        raise ValueError("Search query cannot be empty.")
    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    vector = embed_text(query, "RETRIEVAL_QUERY")
    _, index = get_clients()

    results = index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True,
    )

    return [
        {
            "title": match.metadata.get("title", ""),
            "text": match.metadata.get("text", ""),
            "source": match.metadata.get("source", ""),
            "url": match.metadata.get("url", ""),
            "score": match.score,
        }
        for match in results.matches
    ]




def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    """Split long research papers into overlapping text chunks."""

    if not text or not text.strip():
        raise ValueError("Paper text cannot be empty.")

    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunk size or overlap.")

    chunks = []
    step = chunk_size - overlap

    for start in range(0, len(text), step):
        chunk = text[start:start + chunk_size]

        if chunk.strip():
            chunks.append(chunk)

        if start + chunk_size >= len(text):
            break

    return chunks

