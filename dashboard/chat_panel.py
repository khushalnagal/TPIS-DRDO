# dashboard/chat_panel.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from langchain_ollama import OllamaLLM
from pipeline.embedder import get_embedding
from pipeline.vector_store import query_similar
from config import LLM_MODEL

# ── LLM Instance ────────────────────────────────────────
llm = OllamaLLM(model=LLM_MODEL)


def build_context(chunks: list[str], metadatas: list[dict]) -> str:
    """
    Builds context string from retrieved chunks.
    Includes source filename for citation.
    """
    context_parts = []
    for chunk, meta in zip(chunks, metadatas):
        source = meta.get("filename", "unknown")
        context_parts.append(f"[Source: {source}]\n{chunk}")
    return "\n\n".join(context_parts)

def rag_query(question: str, chat_history: list[dict] = None, n_results: int = 5) -> dict:
    """
    Full RAG pipeline with edge case handling.
    Automatically pulls more context for broad/comparison questions.
    """
    # Edge case — empty question
    if not question or not question.strip():
        return {
            "answer": "Please ask a question.",
            "sources": [],
            "chunks_used": 0
        }

    # Detect broad/comparison questions — pull more chunks for better coverage
    broad_keywords = [
        "all reports", "compare", "every report", "across reports",
        "which report", "all trainees", "rank", "best report",
        "worst report", "overall", "summary of all"
    ]
    if any(kw in question.lower() for kw in broad_keywords):
        n_results = 20
        print(f"  Broad question detected — pulling {n_results} chunks")

    try:
        # Step 1 — Embed question
        query_embedding = get_embedding(question)
    except Exception as e:
        return {
            "answer": f"⚠️ Could not process your question — embedding service may be down. ({e})",
            "sources": [],
            "chunks_used": 0
        }

    try:
        # Step 2 — Retrieve similar chunks
        results = query_similar(query_embedding, n_results=n_results)
        chunks    = results["documents"][0]
        metadatas = results["metadatas"][0]
    except Exception as e:
        return {
            "answer": f"⚠️ Could not search the database. ({e})",
            "sources": [],
            "chunks_used": 0
        }

    # Edge case — no reports in DB yet
    if not chunks:
        return {
            "answer": "No reports have been processed yet. Please upload and process a report first.",
            "sources": [],
            "chunks_used": 0
        }

    # Step 3 — Build context
    context = build_context(chunks, metadatas)

    # Build conversation history string
    history_str = ""
    if chat_history:
        for turn in chat_history[-3:]:
            history_str += f"User: {turn['question']}\nAssistant: {turn['answer']}\n\n"

    # Step 4 — Generate answer
    prompt = f"""You are an AI assistant helping DRDO scientists analyze trainee reports.
Answer the question using ONLY the context below. If the answer isn't in the context, say so clearly.
Always mention which report(s) you used to answer.
If asked to compare or rank reports, note that for precise score rankings, the Dashboard's
Score Distribution and Cohort Overview panels give exact numbers — this chat is best for
content-level questions.

Previous conversation:
{history_str}

Context from trainee reports:
{context}

Question: {question}

Answer:"""

    try:
        answer = llm.invoke(prompt).strip()
    except Exception as e:
        return {
            "answer": f"⚠️ The AI model failed to respond. Is Ollama running? ({e})",
            "sources": [],
            "chunks_used": 0
        }

    # Step 5 — Collect unique sources
    sources = list(set(meta.get("filename", "unknown") for meta in metadatas))

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(chunks)
    }

# ── Streamlit UI ─────────────────────────────────────────
def render_chat_panel():
    """Renders the RAG chat UI in Streamlit."""
    st.subheader("💬 RAG Chat — Ask About Any Report")

    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display chat history
    for turn in st.session_state.chat_history:
        with st.chat_message("user"):
            st.write(turn["question"])
        with st.chat_message("assistant"):
            st.write(turn["answer"])
            if turn["sources"]:
                st.caption(f"📎 Sources: {', '.join(turn['sources'])}")

    # Chat input
    question = st.chat_input("Ask a question about any trainee report...")

    if question:
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Searching reports..."):
                result = rag_query(question, st.session_state.chat_history)
                st.write(result["answer"])
                if result["sources"]:
                    st.caption(f"📎 Sources: {', '.join(result['sources'])}")

        # Save to history
        st.session_state.chat_history.append({
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"]
        })


# ── Test (standalone, terminal mode) ─────────────────────
if __name__ == "__main__":
    print("Testing RAG chat (terminal mode)...\n")

    test_questions = [
        "What dataset was used in the report?",
        "What was the accuracy or key result?",
        "What tools or technologies were used?"
    ]

    chat_history = []

    for q in test_questions:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        print("="*60)

        result = rag_query(q, chat_history)

        print(f"\nA: {result['answer']}")
        print(f"\n📎 Sources: {result['sources']}")
        print(f"📊 Chunks used: {result['chunks_used']}")

        chat_history.append({
            "question": q,
            "answer": result["answer"],
            "sources": result["sources"]
        })

    print(f"\n\n✅ RAG chat works!")