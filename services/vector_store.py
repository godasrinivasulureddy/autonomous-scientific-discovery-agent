
import os

from dotenv import load_dotenv
from google import genai
from pinecone import Pinecone

load_dotenv()

INDEX_NAME = "scientific-papers"
EMBEDDING_MODEL = "gemini-embedding-001"
DIMENSION = 768
BATCH_SIZE = 50


def get_clients():
    """Connect to Gemini embeddings and Pinecone."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    pinecone_key = os.getenv("PINECONE_API_KEY")

    if not gemini_key or not pinecone_key:
        raise ValueError(
            "GEMINI_API_KEY and PINECONE_API_KEY are required."
        )

    gemini_client = genai.Client(api_key=gemini_key)
    pinecone_client = Pinecone(api_key=pinecone_key)

    return gemini_client, pinecone_client.Index(INDEX_NAME)


def embed_text(text, task_type):
    """Generate a 768-dimensional Gemini embedding."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Text cannot be empty.")

    if task_type not in {"RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"}:
        raise ValueError("Unsupported embedding task type.")

    gemini_client, _ = get_clients()

    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config={
            "task_type": task_type,
            "output_dimensionality": DIMENSION,
        },
    )

    if not response.embeddings or not response.embeddings[0].values:
        raise ValueError("Embedding generation returned no vector.")

    embedding = response.embeddings[0].values

    if len(embedding) != DIMENSION:
        raise ValueError(
            f"Expected an embedding of {DIMENSION} dimensions."
        )

    return embedding


def paper_exists(paper_id):
    """Check whether the first chunk of a paper exists in Pinecone."""
    if not isinstance(paper_id, str) or not paper_id.strip():
        raise ValueError("Paper ID is required.")

    _, index = get_clients()
    vector_id = f"{paper_id}-chunk-0"
    response = index.fetch(ids=[vector_id])

    return vector_id in response.vectors


def store_paper(
    paper_id,
    title,
    text,
    source,
    url="",
    publication_types=None,
    peer_review_status="unverified",
):
    """Chunk a paper and store its evidence and citation metadata."""
    if not isinstance(paper_id, str) or not paper_id.strip():
        raise ValueError("Paper ID is required.")

    if not isinstance(title, str) or not title.strip():
        raise ValueError("Paper title is required.")

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Paper text is required.")

    if not isinstance(source, str) or not source.strip():
        raise ValueError("Paper source is required.")

    if not isinstance(url, str):
        raise ValueError("Paper URL must be a string.")

    if publication_types is None:
        publication_types = []

    if (
        not isinstance(publication_types, list)
        or any(not isinstance(item, str) for item in publication_types)
    ):
        raise ValueError("publication_types must be a list of strings.")

    if (
        not isinstance(peer_review_status, str)
        or not peer_review_status.strip()
    ):
        raise ValueError("peer_review_status must be a non-empty string.")

    chunks = chunk_text(text)
    _, index = get_clients()
    vectors = []

    for chunk_number, chunk in enumerate(chunks):
        embedding = embed_text(chunk, "RETRIEVAL_DOCUMENT")

        vectors.append({
            "id": f"{paper_id}-chunk-{chunk_number}",
            "values": embedding,
            "metadata": {
                "paper_id": paper_id,
                "chunk_number": chunk_number,
                "title": title.strip(),
                "text": chunk,
                "source": source.strip(),
                "url": url.strip(),
                "publication_types": publication_types,
                "peer_review_status": peer_review_status.strip(),
            },
        })

    for start in range(0, len(vectors), BATCH_SIZE):
        index.upsert(vectors=vectors[start:start + BATCH_SIZE])

    return {
        "status": "stored",
        "paper_id": paper_id,
        "chunk_count": len(chunks),
    }


def search_papers(query, top_k=3, peer_reviewed_only=False):
    """Retrieve research chunks, optionally requiring verified peer review."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if (
        not isinstance(top_k, int)
        or isinstance(top_k, bool)
        or top_k < 1
    ):
        raise ValueError("top_k must be a positive integer.")

    if not isinstance(peer_reviewed_only, bool):
        raise ValueError("peer_reviewed_only must be a boolean.")

    vector = embed_text(query, "RETRIEVAL_QUERY")
    _, index = get_clients()

    query_args = {
        "vector": vector,
        "top_k": top_k,
        "include_metadata": True,
    }

    if peer_reviewed_only:
        query_args["filter"] = {
            "peer_review_status": {"$eq": "verified"}
        }

    results = index.query(**query_args)
    papers = []

    for match in results.matches:
        metadata = match.metadata or {}

        paper_id = metadata.get("paper_id")
        chunk_number = metadata.get("chunk_number")
        title = metadata.get("title")
        text = metadata.get("text")
        source = metadata.get("source")
        url = metadata.get("url")
        publication_types = metadata.get("publication_types")
        peer_review_status = metadata.get("peer_review_status")

        papers.append({
            "paper_id": paper_id if isinstance(paper_id, str) else "",
            "chunk_number": (
                chunk_number
                if isinstance(chunk_number, int)
                and not isinstance(chunk_number, bool)
                and chunk_number >= 0
                else 0
            ),
            "title": title if isinstance(title, str) else "",
            "text": text if isinstance(text, str) else "",
            "source": source if isinstance(source, str) else "",
            "url": url if isinstance(url, str) else "",
            "publication_types": (
                publication_types
                if isinstance(publication_types, list)
                and all(isinstance(item, str) for item in publication_types)
                else []
            ),
            "peer_review_status": (
                peer_review_status
                if isinstance(peer_review_status, str)
                else "unverified"
            ),
            "score": match.score,
        })

    return papers


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[str]:
    """Split research text into overlapping chunks."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Paper text cannot be empty.")

    if (
        not isinstance(chunk_size, int)
        or isinstance(chunk_size, bool)
        or not isinstance(overlap, int)
        or isinstance(overlap, bool)
        or chunk_size <= 0
        or overlap < 0
        or overlap >= chunk_size
    ):
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

