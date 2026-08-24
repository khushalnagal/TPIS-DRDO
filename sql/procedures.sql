-- =============================================================================
-- TPIS · procedures.sql
-- =============================================================================

USE tpis;

DELIMITER $$

-- 1. Flag at-risk trainees
CREATE PROCEDURE sp_flag_at_risk()
BEGIN
    SELECT
        t.name,
        c.cohort_name,
        s.total,
        s.methodology,
        r.filename
    FROM trainees t
    JOIN cohorts  c ON c.cohort_id  = t.cohort_id
    JOIN reports  r ON r.trainee_id = t.trainee_id
    JOIN scores   s ON s.report_id  = r.report_id
    WHERE s.total < 60 OR s.methodology < 50
    ORDER BY s.total ASC;
END$$

-- 2. Get full cohort report
CREATE PROCEDURE sp_generate_cohort_report(
    IN p_cohort_name VARCHAR(100)
)
BEGIN
    SELECT
        t.name,
        s.technical_depth,
        s.clarity,
        s.methodology,
        s.results,
        s.references_score,
        s.total,
        s.feedback
    FROM trainees t
    JOIN cohorts  c ON c.cohort_id  = t.cohort_id
    JOIN reports  r ON r.trainee_id = t.trainee_id
    JOIN scores   s ON s.report_id  = r.report_id
    WHERE c.cohort_name = p_cohort_name
    ORDER BY s.total DESC;
END$$

DELIMITER ;
