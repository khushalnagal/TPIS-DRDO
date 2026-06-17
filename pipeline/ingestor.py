# pipeline/ingestor.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pypdf
import pdfplumber
from config import UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ── Text Splitter ───────────────────────────────────────
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
)


def extract_text_pypdf(pdf_path: str) -> str:
    """Extract text using pypdf."""
    text = ""
    with open(pdf_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text.strip()


def extract_text_pdfplumber(pdf_path: str) -> str:
    """Extract text using pdfplumber (better for tables)."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()


def extract_text(pdf_path: str) -> str:
    """
    Main extraction function.
    Tries pypdf first, then pdfplumber fallback.
    """
    pdf_path = str(pdf_path)
    print(f"  Extracting text from: {Path(pdf_path).name}")

    # Try pypdf first
    text = extract_text_pypdf(pdf_path)

    # If empty try pdfplumber
    if not text.strip():
        print("  pypdf returned empty — trying pdfplumber...")
        text = extract_text_pdfplumber(pdf_path)

    if not text.strip():
        raise ValueError(f"Could not extract text from {pdf_path}")

    print(f"  Extracted {len(text)} characters")
    return text


def chunk_text(text: str) -> list[str]:
    """Split text into chunks for embedding."""
    chunks = splitter.split_text(text)
    print(f"  Created {len(chunks)} chunks")
    return chunks


def ingest_pdf(pdf_path: str) -> dict:
    """
    Full ingestion pipeline for one PDF.
    Returns text and chunks ready for embedding.
    """
    text = extract_text(pdf_path)
    chunks = chunk_text(text)

    return {
        "filename": Path(pdf_path).name,
        "text": text,
        "chunks": chunks,
        "num_chunks": len(chunks),
        "num_chars": len(text)
    }


# ── Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing ingestor...\n")

    pdfs = list(UPLOAD_DIR.glob("*.pdf"))

    if not pdfs:
        print(f"No PDFs found in {UPLOAD_DIR}")
        print("Drop any PDF into data/uploads/ and run again.")
    else:
        pdf_path = pdfs[0]
        print(f"Found PDF: {pdf_path.name}\n")

        result = ingest_pdf(str(pdf_path))

        print(f"\nResults:")
        print(f"  Filename   : {result['filename']}")
        print(f"  Characters : {result['num_chars']}")
        print(f"  Chunks     : {result['num_chunks']}")
        print(f"\nFirst chunk preview:")
        print(f"  {result['chunks'][0][:200]}...")
        print(f"\n✅ Ingestor works!")