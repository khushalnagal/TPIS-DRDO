-- =============================================================================
-- TPIS · procedures.sql
-- =============================================================================

USE tpis;

DELIMITER $$

-- 1. Insert scores after LLM scoring
CREATE PROCEDURE sp_score_report(
    IN p_report_id       INT,
    IN p_technical_depth INT,
    IN p_clarity         INT,
    IN p_methodology     INT,
    IN p_results         INT,
    IN p_references      INT,
    IN p_total           INT,
    IN p_feedback        TEXT
)
BEGIN
    INSERT INTO scores (
        report_id, technical_depth, clarity,
        methodology, results, references_score,
        total, feedback
    ) VALUES (
        p_report_id, p_technical_depth, p_clarity,
        p_methodology, p_results, p_references,
        p_total, p_feedback
    );

    -- Mark report as scored
    UPDATE reports
    SET status = 'scored'
    WHERE report_id = p_report_id;
END$$

-- 2. Flag at-risk trainees
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

-- 3. Get full cohort report
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