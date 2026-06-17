# pipeline/summarizer.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from langchain_ollama import OllamaLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import LLM_MODEL, CHUNK_SIZE, CHUNK_OVERLAP

# ── LLM Instance ────────────────────────────────────────
llm = OllamaLLM(model=LLM_MODEL)

# ── Text Splitter ───────────────────────────────────────
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
)


def split_text(text: str) -> list[str]:
    """Split long text into chunks."""
    chunks = splitter.split_text(text)
    print(f"  Split into {len(chunks)} chunks")
    return chunks


def summarize_chunk(chunk: str) -> str:
    """Summarize a single chunk of text."""
    prompt = f"""Summarize the following section of a research report in 2-3 sentences.
Focus on key findings, methods, and results only.

Text:
{chunk}

Summary:"""
    return llm.invoke(prompt).strip()


def summarize_report(text: str) -> str:
    """
    Full map-reduce summarization of a report.

    MAP    → summarize each chunk individually
    REDUCE → combine all summaries into one final summary
    """
    print("  Step 1 · Splitting text...")
    chunks = split_text(text)

    # MAP — summarize each chunk
    print(f"  Step 2 · Summarizing {len(chunks)} chunks (MAP)...")
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        print(f"    Chunk {i+1}/{len(chunks)}...")
        summary = summarize_chunk(chunk)
        chunk_summaries.append(summary)

    # REDUCE — combine all summaries
    print("  Step 3 · Combining summaries (REDUCE)...")
    combined = "\n".join(chunk_summaries)

    reduce_prompt = f"""You are reviewing a DRDO trainee research report.
Below are summaries of different sections of the report.
Write a single coherent summary of the entire report in 4-5 sentences.
Cover: main objective, methodology, key results, and conclusion.

Section Summaries:
{combined}

Final Summary:"""

    final_summary = llm.invoke(reduce_prompt).strip()
    return final_summary


# ── Test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing summarizer...\n")

    # Simulate a short report text
    sample_text = """
    Abstract:
    This report presents a study on target detection using deep learning
    techniques applied to radar signal data collected at DRDO facilities.

    Introduction:
    Target detection in radar systems is a critical challenge in defence
    applications. Traditional signal processing methods often fail under
    noisy conditions. This study explores the use of Convolutional Neural
    Networks (CNN) to improve detection accuracy.

    Methodology:
    We collected 5000 radar signal samples, split into 80% training and
    20% testing sets. A CNN architecture with 4 convolutional layers was
    designed and trained for 50 epochs using the Adam optimizer with a
    learning rate of 0.001. Data augmentation techniques were applied to
    improve generalization.

    Results:
    The CNN model achieved 91.3% detection accuracy on the test set,
    outperforming the traditional CFAR detector which achieved 78.2%.
    False positive rate was reduced by 34% compared to baseline.
    Training converged after 38 epochs.

    Conclusion:
    Deep learning based target detection significantly outperforms
    traditional methods on radar data. Future work will focus on
    real-time deployment on embedded hardware for field applications.

    References:
    1. LeCun, Y. et al. (1998). Gradient-based learning applied to document recognition.
    2. Wen, L. et al. (2020). Deep learning for radar target detection.
    3. Richards, M.A. (2014). Fundamentals of Radar Signal Processing.
    """

    print("Input: Sample DRDO radar detection report\n")
    print("Running map-reduce summarization...")
    print("-" * 50)

    summary = summarize_report(sample_text)

    print("\n" + "=" * 50)
    print("FINAL SUMMARY:")
    print("=" * 50)
    print(summary)
    print("\n✅ Summarizer works!")