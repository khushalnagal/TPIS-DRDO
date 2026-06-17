# pipeline/embedder.py
# NEW
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import ollama
from config import EMBED_MODEL

def get_embedding(text: str) -> list[float]:
    """
    Takes a text string.
    Returns a list of floats (the embedding vector).
    """
    response = ollama.embeddings(
        model=EMBED_MODEL,
        prompt=text
    )
    return response["embedding"]


def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Takes a list of text strings.
    Returns a list of embedding vectors.
    """
    embeddings = []
    for i, text in enumerate(texts):
        print(f"  Embedding chunk {i+1}/{len(texts)}...")
        embedding = get_embedding(text)
        embeddings.append(embedding)
    return embeddings


if __name__ == "__main__":
    print("Testing embedder...\n")

    # Test 1 — single embedding
    test_text = "This report analyzes the performance of a neural network on image classification."
    print(f"Input text: {test_text}\n")

    embedding = get_embedding(test_text)

    print(f"Embedding type  : {type(embedding)}")
    print(f"Embedding length: {len(embedding)}")
    print(f"First 5 values  : {embedding[:5]}")
    print(f"\n✅ Single embedding works!\n")

    # Test 2 — batch embeddings
    test_texts = [
        "The methodology used Random Forest for classification.",
        "Results show 92% accuracy on the test dataset.",
        "References include papers from IEEE and Springer."
    ]

    print(f"Testing batch of {len(test_texts)} texts...")
    embeddings = get_embeddings_batch(test_texts)

    print(f"\nTotal embeddings : {len(embeddings)}")
    print(f"Each vector size : {len(embeddings[0])}")
    print(f"\n✅ Batch embedding works!")