# pipeline/vector_store.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
os.environ["ANONYMIZED_TELEMETRY"] = "False" 

import chromadb
from config import CHROMA_DIR, CHROMA_COLLECTION

# ── Singleton Client ────────────────────────────────────
_client = None

def get_client() -> chromadb.PersistentClient:
    """
    Returns a single ChromaDB client instance.
    Never open two clients at the same time.
    """
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return _client


def get_collection():
    """
    Returns the TPIS collection from ChromaDB.
    Creates it if it doesn't exist.
    """
    client = get_client()
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def add_chunks(chunks: list[str], embeddings: list[list[float]], metadata: list[dict]):
    """
    Adds text chunks + their embeddings to ChromaDB.

    chunks     : list of text strings
    embeddings : list of vectors (from embedder.py)
    metadata   : list of dicts e.g. {"report_id": 1, "filename": "report.pdf"}
    """
    collection = get_collection()

    # Generate unique IDs for each chunk
    existing = collection.count()
    ids = [f"chunk_{existing + i}" for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadata,
        ids=ids
    )
    print(f"  ✅ Added {len(chunks)} chunks to ChromaDB")


def query_similar(query_embedding: list[float], n_results: int = 5) -> dict:
    """
    Given a query embedding, finds the most similar chunks.
    Returns the top n_results matches.
    """
    collection = get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )
    return results


def get_collection_count() -> int:
    """Returns total number of chunks stored."""
    return get_collection().count()


def reset_collection():
    """Deletes and recreates the collection. Use carefully."""
    client = get_client()
    client.delete_collection(name=CHROMA_COLLECTION)
    print("  ✅ Collection reset.")


# ── Test ────────────────────────────────────────────────
if __name__ == "__main__":
    from embedder import get_embedding, get_embeddings_batch

    print("Testing vector_store...\n")

    # Sample chunks simulating a real report
    sample_chunks = [
        "The study used a Convolutional Neural Network for image recognition.",
        "Dataset consisted of 10,000 labelled images from CIFAR-10.",
        "The model achieved 94% accuracy on the validation set.",
        "Random Forest was used as a baseline comparison model.",
        "References include LeCun et al. 1998 and Krizhevsky et al. 2012."
    ]

    sample_metadata = [
        {"report_id": "1", "filename": "report_01.pdf", "chunk_index": str(i)}
        for i in range(len(sample_chunks))
    ]

    # Step 1 — Embed
    print("Step 1 · Embedding chunks...")
    embeddings = get_embeddings_batch(sample_chunks)

    # Step 2 — Store
    print("\nStep 2 · Storing in ChromaDB...")
    add_chunks(sample_chunks, embeddings, sample_metadata)

    # Step 3 — Query
    print("\nStep 3 · Querying ChromaDB...")
    query = "What accuracy did the model achieve?"
    print(f"Query: '{query}'")

    query_embedding = get_embedding(query)
    results = query_similar(query_embedding, n_results=3)

    print(f"\nTop 3 similar chunks:")
    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        print(f"\n  [{i+1}] Score: {1 - dist:.3f}")
        print(f"       File : {meta['filename']}")
        print(f"       Text : {doc[:80]}...")

    print(f"\nTotal chunks in DB : {get_collection_count()}")
    print(f"\n✅ vector_store works!")