# =============================================================================
# TPIS · app.py
# Main entry point — ties ingestor.py + scorer.py + db_writer.py together
#
# Usage:
#   python app.py path/to/report.pdf "Trainee Name" "Cohort Name"
#   python app.py --batch "Cohort Name"   (processes all PDFs in data/uploads/)
# =============================================================================

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from pipeline.ingestor import ingest_pdf
from pipeline.scorer import score_report
from pipeline.db_writer import save_report
import config


def process_single_report(pdf_path: str, trainee_name: str, cohort_name: str):
    """
    Full pipeline for ONE report:
    PDF → extract text → score with LLM → save to MySQL
    """
    pdf_path = str(pdf_path)
    filename = Path(pdf_path).name

    print(f"\n{'=' * 60}")
    print(f"Processing: {filename}")
    print(f"Trainee: {trainee_name}  |  Cohort: {cohort_name}")
    print(f"{'=' * 60}")

    # Step 1 — Ingest (extract text + chunk)
    print("\n[1/3] Extracting text...")
    ingested = ingest_pdf(pdf_path)
    print(f"  ✅ Extracted {ingested['num_chars']} characters, {ingested['num_chunks']} chunks")

    # Step 2 — Score with LLM
    print("\n[2/3] Scoring with LLM...")
    scores = score_report(ingested["text"], filename=filename)
    print(f"  ✅ Total score: {scores['total']}/100")

    # Step 3 — Save to MySQL
    print("\n[3/3] Saving to database...")
    report_id = save_report(
        trainee_name=trainee_name,
        cohort_name=cohort_name,
        filename=filename,
        scores=scores
    )

    if report_id:
        print(f"\n✅ DONE — Report ID {report_id} saved successfully.")
    else:
        print(f"\n⚠️  Report was not saved (duplicate or error — see above).")

    return report_id


def process_batch(cohort_name: str, trainee_name_map: dict = None):
    """
    Processes every PDF in data/uploads/.

    trainee_name_map: optional dict mapping filename -> trainee name.
    If not provided, uses the filename (without extension) as the trainee name.
    Example: {"arjun_report.pdf": "Arjun Sharma"}
    """
    pdfs = list(config.UPLOAD_DIR.glob("*.pdf"))

    if not pdfs:
        print(f"No PDFs found in {config.UPLOAD_DIR}")
        return []

    print(f"Found {len(pdfs)} PDF(s) to process.\n")

    results = []
    for pdf_path in pdfs:
        filename = pdf_path.name
        trainee_name = (trainee_name_map or {}).get(filename, pdf_path.stem.replace("_", " ").title())

        try:
            report_id = process_single_report(str(pdf_path), trainee_name, cohort_name)
            results.append({"filename": filename, "report_id": report_id, "status": "success" if report_id else "skipped"})
        except Exception as e:
            print(f"\n⚠️  Failed to process {filename}: {e}")
            results.append({"filename": filename, "report_id": None, "status": "failed", "error": str(e)})

    # Summary
    print(f"\n{'=' * 60}")
    print("BATCH SUMMARY")
    print(f"{'=' * 60}")
    for r in results:
        print(f"  {r['filename']:<35} {r['status']}")

    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print('  python app.py path/to/report.pdf "Trainee Name" "Cohort Name"')
        print('  python app.py --batch "Cohort Name"')
        sys.exit(1)

    if sys.argv[1] == "--batch":
        if len(sys.argv) < 3:
            print('Usage: python app.py --batch "Cohort Name"')
            sys.exit(1)
        cohort = sys.argv[2]
        process_batch(cohort)

    else:
        if len(sys.argv) < 4:
            print('Usage: python app.py path/to/report.pdf "Trainee Name" "Cohort Name"')
            sys.exit(1)

        pdf_file = sys.argv[1]
        trainee = sys.argv[2]
        cohort = sys.argv[3]

        process_single_report(pdf_file, trainee, cohort)