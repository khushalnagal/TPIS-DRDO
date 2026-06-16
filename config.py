# =============================================================================
# TPIS · config.py
# Central configuration — all modules import from here
# =============================================================================
from pathlib import Path
from urllib.parse import quote_plus
from pathlib import Path

# ── Project Root ──────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).resolve().parent
DATA_DIR   = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma_db"
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# ── Database (MySQL) ──────────────────────────────────────────────────────────
DB_HOST     = "localhost"
DB_PORT     = 3306
DB_NAME     = "tpis"
DB_USER     = "root"
DB_PASSWORD = "KHUSHALnagal@05#"    

DB_URL = f"mysql+mysqlconnector://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ── Ollama / LLM (Sukhdev's machine) ─────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL       = "llama3.2"
EMBED_MODEL     = "nomic-embed-text"

# ── Text Chunking ─────────────────────────────────────────────────────────────
CHUNK_SIZE    = 512
CHUNK_OVERLAP = 64

# ── Scoring ───────────────────────────────────────────────────────────────────
SCORE_WEIGHTS = {
    "technical_depth": 25,
    "clarity":         20,
    "methodology":     20,
    "results":         25,
    "references":      10,
}

AT_RISK_THRESHOLD     = 60
METHODOLOGY_THRESHOLD = 50

# ── Integration Contract ──────────────────────────────────────────────────────
# Sukhdev's scorer.py MUST return exactly these keys
# Your db_writer.py expects exactly these keys
SCORE_KEYS = [
    "technical_depth",
    "clarity",
    "methodology",
    "results",
    "references",
    "total",
    "feedback",
    "keywords",
]

# ── ChromaDB ──────────────────────────────────────────────────────────────────
CHROMA_COLLECTION = "tpis_reports"

# ── OCR ───────────────────────────────────────────────────────────────────────
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
OCR_DPI       = 300
OCR_LANGUAGE  = "eng"

# ── Streamlit ─────────────────────────────────────────────────────────────────
APP_TITLE = "TPIS · Trainee Performance Intelligence System"
APP_ICON  = "🧠"

# ── Verify ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"BASE_DIR   : {BASE_DIR}")
    print(f"UPLOAD_DIR : {UPLOAD_DIR}")
    print(f"CHROMA_DIR : {CHROMA_DIR}")
    print(f"DB_URL     : {DB_URL}")
    print(f"LLM_MODEL  : {LLM_MODEL}")



# ---------------------------------------------------------------------------    
from pathlib import Path
from urllib.parse import quote_plus

DB_HOST     = "localhost"
DB_PORT     = 3306
DB_NAME     = "tpis"
DB_USER     = "root"
DB_PASSWORD = "KHUSHALnagal@05#"

DB_URL = f"mysql+mysqlconnector://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"