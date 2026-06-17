# =============================================================================
# TPIS · pipeline/db_writer.py
# Receives scores from Sukhdev's scorer.py → writes everything to MySQL
# =============================================================================
 
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
 
# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    f"mysql+mysqlconnector://{config.DB_USER}:{quote_plus(config.DB_PASSWORD)}"
    f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}",
    pool_pre_ping=True
)
 
# ── Duplicate Check ───────────────────────────────────────────────────────────
def report_already_exists(filename: str) -> bool:
    """Check if a report with this filename has already been scored."""
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT report_id FROM reports WHERE filename = :fn"),
                {"fn": filename}
            ).fetchone()
            return row is not None
    except SQLAlchemyError as e:
        print(f"⚠️ Database error while checking duplicates: {e}")
        return False
 
# ── Cohort ────────────────────────────────────────────────────────────────────
def get_or_create_cohort(cohort_name: str) -> int:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT cohort_id FROM cohorts WHERE cohort_name = :name"),
            {"name": cohort_name}
        ).fetchone()
        if row:
            return row[0]
        result = conn.execute(
            text("INSERT INTO cohorts (cohort_name) VALUES (:name)"),
            {"name": cohort_name}
        )
        conn.commit()
        return result.lastrowid
 
# ── Trainee ───────────────────────────────────────────────────────────────────
def get_or_create_trainee(name: str, cohort_id: int) -> int:
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT trainee_id FROM trainees WHERE name = :name AND cohort_id = :cid"),
            {"name": name, "cid": cohort_id}
        ).fetchone()
        if row:
            return row[0]
        result = conn.execute(
            text("INSERT INTO trainees (name, cohort_id) VALUES (:name, :cid)"),
            {"name": name, "cid": cohort_id}
        )
        conn.commit()
        return result.lastrowid
 
# ── Report ────────────────────────────────────────────────────────────────────
def create_report(trainee_id: int, filename: str) -> int:
    with engine.connect() as conn:
        result = conn.execute(
            text("INSERT INTO reports (trainee_id, filename, status) VALUES (:tid, :fn, 'processing')"),
            {"tid": trainee_id, "fn": filename}
        )
        conn.commit()
        return result.lastrowid
 
# ── Scores ────────────────────────────────────────────────────────────────────
# NOTE: stored procedure sp_score_report's 5th parameter is named p_references
# in procedures.sql, but it inserts into the references_score COLUMN.
# The Python-side dict key and the bind parameter name below are just labels —
# what matters is positional order matching sp_score_report's signature:
#   (report_id, technical_depth, clarity, methodology, results, references, total, feedback)
def insert_scores(report_id: int, scores: dict):
    with engine.connect() as conn:
        conn.execute(text("""
            CALL sp_score_report(
                :report_id, :technical_depth, :clarity,
                :methodology, :results, :references_val,
                :total, :feedback
            )
        """), {
            "report_id":       report_id,
            "technical_depth": scores.get("technical_depth", 0),
            "clarity":         scores.get("clarity", 0),
            "methodology":     scores.get("methodology", 0),
            "results":         scores.get("results", 0),
            "references_val":  scores.get("references", 0),
            "total":           scores.get("total", 0),
            "feedback":        scores.get("feedback", "")
        })
        conn.commit()
 
# ── Keywords ──────────────────────────────────────────────────────────────────
def insert_keywords(report_id: int, keywords: list):
    with engine.connect() as conn:
        for kw in keywords:
            conn.execute(
                text("INSERT INTO keywords (report_id, keyword) VALUES (:rid, :kw)"),
                {"rid": report_id, "kw": kw}
            )
        conn.commit()
 
# ── Master Function (call this from app.py / Sukhdev's scorer.py) ────────────
def save_report(trainee_name: str, cohort_name: str, filename: str, scores: dict):
    """
    Saves a scored report to MySQL.
    Returns report_id on success, None on failure or duplicate.
    """
    try:
        # 1. Duplicate check — skip if this exact filename was already scored
        if report_already_exists(filename):
            print(f"⏭️  Skipped: '{filename}' already exists in database.")
            return None
 
        # 2. Normal save flow
        cohort_id  = get_or_create_cohort(cohort_name)
        trainee_id = get_or_create_trainee(trainee_name, cohort_id)
        report_id  = create_report(trainee_id, filename)
        insert_scores(report_id, scores)
 
        if scores.get("keywords"):
            insert_keywords(report_id, scores["keywords"])
 
        print(f"✅ Saved: {trainee_name} | {cohort_name} | Score: {scores.get('total')}")
        return report_id
 
    except SQLAlchemyError as e:
        print(f"⚠️ Database error while saving report '{filename}': {e}")
        return None
    except Exception as e:
        print(f"⚠️ Unexpected error while saving report '{filename}': {e}")
        return None
 
# ── Test ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_scores = {
        "technical_depth": 82,
        "clarity":         74,
        "methodology":     68,
        "results":         77,
        "references":      55,
        "total":           75,
        "feedback":        "Good technical depth. Methodology needs improvement.",
        "keywords":        ["logistic regression", "p-value", "ANOVA"]
    }
 
    # First save — should succeed
    rid = save_report(
        trainee_name="Test Trainee 2",
        cohort_name="DRDO-2025",
        filename="test_report_2.pdf",
        scores=test_scores
    )
    print(f"Report ID: {rid}")
 
    # Second save with SAME filename — should be skipped as duplicate
    rid2 = save_report(
        trainee_name="Test Trainee 2",
        cohort_name="DRDO-2025",
        filename="test_report_2.pdf",
        scores=test_scores
    )
    print(f"Report ID (duplicate attempt): {rid2}")
 