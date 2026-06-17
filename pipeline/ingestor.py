# =============================================================================
# TPIS · pipeline/ingestor.py
# PDF text extraction with OCR fallback for scanned documents
# =============================================================================

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pypdf
import pdfplumber
import pytesseract
from pdf2image import convert_from_path

import config
from config import UPLOAD_DIR, CHUNK_SIZE, CHUNK_OVERLAP, TESSERACT_CMD, OCR_DPI, OCR_LANGUAGE
from langchain.text_splitter import RecursiveCharacterTextSplitter

# ── Tesseract Path ────────────────────────────────────────────────────────────
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

# ── Text Splitter ─────────────────────────────────────────────────────────────
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP
)

# ── Extraction methods ────────────────────────────────────────────────────────
def extract_text_pypdf(pdf_path: str) -> str:
    """Extract text using pypdf — fastest, works on digital PDFs."""
    text = ""
    with open(pdf_path, "rb") as f:
        reader = pypdf.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text.strip()

def extract_text_pdfplumber(pdf_path: str) -> str:
    """Extract text using pdfplumber — better for tables/layout."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text.strip()

def extract_text_ocr(pdf_path: str) -> str:
    """
    OCR fallback for scanned PDFs (image-only, no embedded text).
    Converts each page to an image, then runs Tesseract OCR on it.
    """
    print("  No embedded text found — running OCR fallback...")
    text = ""
    pages = convert_from_path(pdf_path, dpi=OCR_DPI)
    for i, page_image in enumerate(pages, start=1):
        page_text = pytesseract.image_to_string(page_image, lang=OCR_LANGUAGE)
        text += page_text + "\n"
        print(f"    OCR page {i}/{len(pages)} done")
    return text.strip()

def extract_text(pdf_path: str) -> str:
    """
    Main extraction function — tries digital extraction first,
    falls back to OCR automatically if the PDF is scanned.
    """
    pdf_path = str(pdf_path)
    print(f"  Extracting text from: {Path(pdf_path).name}")

    # 1. Try pypdf first (fastest)
    text = extract_text_pypdf(pdf_path)

    # 2. If empty, try pdfplumber (handles some edge cases pypdf misses)
    if not text.strip():
        print("  pypdf returned empty — trying pdfplumber...")
        text = extract_text_pdfplumber(pdf_path)

    # 3. If still empty, this is a scanned PDF — use OCR
    if not text.strip():
        text = extract_text_ocr(pdf_path)

    if not text.strip():
        raise ValueError(f"Could not extract any text from {pdf_path} — even OCR failed.")

    print(f"  Extracted {len(text)} characters")
    return text

def chunk_text(text: str) -> list:
    """Split text into overlapping chunks for embedding."""
    chunks = splitter.split_text(text)
    print(f"  Created {len(chunks)} chunks")
    return chunks

# ── Single PDF ────────────────────────────────────────────────────────────────
def ingest_pdf(pdf_path: str, metadata: dict = None) -> dict:
    """
    Full ingestion pipeline for one PDF.
    Returns text and chunks ready for embedding, plus any metadata passed in
    (e.g. trainee_name, cohort_name) so downstream steps don't lose context.
    """
    text = extract_text(pdf_path)
    chunks = chunk_text(text)

    result = {
        "filename":   Path(pdf_path).name,
        "filepath":   str(pdf_path),
        "text":       text,
        "chunks":     chunks,
        "num_chunks": len(chunks),
        "num_chars":  len(text)
    }

    if metadata:
        result["metadata"] = metadata

    return result

# ── Batch processing ──────────────────────────────────────────────────────────
def ingest_batch(upload_dir: Path = None) -> list:
    """
    Process every PDF in the uploads folder.
    Returns a list of ingestion results — failures are logged, not fatal.
    """
    upload_dir = upload_dir or UPLOAD_DIR
    pdfs = list(Path(upload_dir).glob("*.pdf"))

    if not pdfs:
        print(f"No PDFs found in {upload_dir}")
        return []

    results = []
    for pdf_path in pdfs:
        try:
            print(f"\nProcessing: {pdf_path.name}")
            result = ingest_pdf(str(pdf_path))
            results.append(result)
        except Exception as e:
            print(f"  ⚠️ Failed to process {pdf_path.name}: {e}")
            continue

    print(f"\n✅ Batch complete: {len(results)}/{len(pdfs)} PDFs processed successfully")
    return results

# ── Test ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing ingestor...\n")

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Testing specific file: {pdf_path}\n")
        result = ingest_pdf(pdf_path)
        print(f"\nResults:")
        print(f"  Filename   : {result['filename']}")
        print(f"  Characters : {result['num_chars']}")
        print(f"  Chunks     : {result['num_chunks']}")
        print(f"\nFirst chunk preview:")
        print(f"  {result['chunks'][0][:200]}...")
        print(f"\n✅ Ingestor works!")
    else:
        pdfs = list(UPLOAD_DIR.glob("*.pdf"))
        if not pdfs:
            print(f"No PDFs found in {UPLOAD_DIR}")
            print("Drop any PDF into data/uploads/ and run again.")
            print("Or run: python pipeline/ingestor.py path/to/specific.pdf")
        else:
            results = ingest_batch()
            for r in results:
                print(f"\n{r['filename']}: {r['num_chars']} chars, {r['num_chunks']} chunks")