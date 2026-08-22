# TPIS: Trainee Performance Intelligence System

A local-first AI platform that automates the review and scoring of trainee reports, replacing manual PDF grading with an LLM-driven pipeline that extracts, scores, and visualizes trainee performance data.

## Overview

TPIS ingests trainee PDF reports, extracts and chunks their text (with OCR fallback for scanned documents), scores them against a weighted rubric using a local LLM, stores results in MySQL, and surfaces everything through an interactive Streamlit dashboard. Built to run entirely on local infrastructure. No external API calls, no cloud dependency.

## Features

- **PDF ingestion**: text extraction via `pypdf`/`pdfplumber`, with Tesseract OCR fallback for scanned reports
- **LLM-based scoring**: rubric-driven evaluation (technical depth, clarity, methodology, results, references) via a local Ollama model
- **Semantic search**: report embeddings stored in ChromaDB for similarity search and Q&A
- **Structured storage**: cohorts, trainees, reports, and scores persisted in MySQL
- **Interactive dashboard**: Streamlit app with trainee cards, keyword clouds, charts, and a chat panel
- **CSV export**: one-command export of scored results

## Tech Stack

| Layer | Tools |
|---|---|
| LLM & Orchestration | LangChain, Ollama |
| Vector Store | ChromaDB |
| PDF Processing | pypdf, pdfplumber, pytesseract, pdf2image |
| Database | MySQL, SQLAlchemy |
| Dashboard | Streamlit, Plotly |
| Data | pandas, numpy |

## Project Structure

```
TPIS-DRDO/
├── app.py                 # Main pipeline entry point
├── config.py               # Central configuration
├── export_csv.py            # Export scored results to CSV
├── pipeline/
│   ├── ingestor.py          # PDF text extraction + chunking
│   ├── scorer.py             # LLM-based rubric scoring
│   ├── summarizer.py          # Report summarization
│   ├── embedder.py            # Embedding generation
│   ├── vector_store.py         # ChromaDB interface
│   └── db_writer.py            # MySQL persistence
├── dashboard/
│   ├── overview.py            # Main Streamlit dashboard
│   ├── trainee_cards.py        # Per-trainee summary cards
│   ├── charts.py               # Score visualizations
│   ├── keyword_cloud.py         # Keyword frequency cloud
│   └── chat_panel.py            # Chat-over-reports interface
├── sql/
│   ├── schema.sql              # Table definitions
│   ├── views.sql                # Reporting views
│   └── procedures.sql            # Stored procedures
└── tests/
    ├── test_pipeline.py
    └── test_scoring.py
```

## Setup

### Prerequisites
- Python 3.10+
- MySQL Server
- [Ollama](https://ollama.com) running locally with `llama3.2` and `nomic-embed-text` pulled
- Tesseract OCR (for scanned PDF support)

### Installation

```bash
git clone https://github.com/<your-username>/TPIS-DRDO.git
cd TPIS-DRDO
python -m venv tpis_env
source tpis_env/bin/activate   # Windows: tpis_env\Scripts\activate
pip install -r requirements.txt
```

### Configuration

Copy the config template and set your own values (DB credentials, Tesseract path, model names). **Do not commit real credentials**:

```bash
cp config.py.example config.py   # or edit config.py directly, then keep it out of git
```

Create the database:

```bash
mysql -u root -p < sql/schema.sql
mysql -u root -p < sql/views.sql
mysql -u root -p < sql/procedures.sql
```

### Usage

Process a single report:
```bash
python app.py path/to/report.pdf "Trainee Name" "Cohort Name"
```

Batch-process all PDFs in `data/uploads/`:
```bash
python app.py --batch "Cohort Name"
```

Launch the dashboard:
```bash
streamlit run dashboard/overview.py
```

Export results to CSV:
```bash
python export_csv.py
```

## Scoring Rubric

Reports are scored out of 100 across five weighted criteria:

| Criterion | Weight |
|---|---|
| Technical Depth | 25 |
| Results | 25 |
| Clarity | 20 |
| Methodology | 20 |
| References | 10 |

Reports scoring below the configured threshold are flagged as at-risk for follow-up.
