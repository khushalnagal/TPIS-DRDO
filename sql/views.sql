-- =============================================================================
-- TPIS · views.sql
-- =============================================================================

USE tpis;

-- 1. Cohort Performance Summary
CREATE OR REPLACE VIEW vw_cohort_summary AS
SELECT
    c.cohort_name,
    COUNT(DISTINCT t.trainee_id)               AS total_trainees,
    ROUND(AVG(s.total), 1)                     AS avg_score,
    MAX(s.total)                               AS top_score,
    MIN(s.total)                               AS lowest_score,
    SUM(CASE WHEN s.total < 60 THEN 1 ELSE 0 END) AS at_risk_count
FROM cohorts c
JOIN trainees t  ON t.cohort_id  = c.cohort_id
JOIN reports  r  ON r.trainee_id = t.trainee_id
JOIN scores   s  ON s.report_id  = r.report_id
GROUP BY c.cohort_name;

-- 2. Trainee Score Breakdown
CREATE OR REPLACE VIEW vw_trainee_scores AS
SELECT
    t.name                AS trainee_name,
    c.cohort_name,
    s.technical_depth,
    s.clarity,
    s.methodology,
    s.results,
    s.references_score,
    s.total,
    s.feedback,
    r.filename,
    s.scored_at
FROM trainees t
JOIN cohorts  c  ON c.cohort_id  = t.cohort_id
JOIN reports  r  ON r.trainee_id = t.trainee_id
JOIN scores   s  ON s.report_id  = r.report_id;

-- 3. Skill Gap Matrix
CREATE OR REPLACE VIEW vw_skill_gaps AS
SELECT
    c.cohort_name,
    ROUND(AVG(s.technical_depth), 1)  AS avg_technical_depth,
    ROUND(AVG(s.clarity), 1)          AS avg_clarity,
    ROUND(AVG(s.methodology), 1)      AS avg_methodology,
    ROUND(AVG(s.results), 1)          AS avg_results,
    ROUND(AVG(s.references_score), 1) AS avg_references
FROM cohorts c
JOIN trainees t ON t.cohort_id = c.cohort_id
JOIN reports  r ON r.trainee_id = t.trainee_id
JOIN scores   s ON s.report_id  = r.report_id
GROUP BY c.cohort_name;

-- 4. At-Risk Trainees
CREATE OR REPLACE VIEW vw_at_risk AS
SELECT
    t.name           AS trainee_name,
    c.cohort_name,
    s.total,
    s.methodology,
    s.feedback,
    r.filename
FROM trainees t
JOIN cohorts  c ON c.cohort_id  = t.cohort_id
JOIN reports  r ON r.trainee_id = t.trainee_id
JOIN scores   s ON s.report_id  = r.report_id
WHERE s.total < 60 OR s.methodology < 50;

-- 5. Keyword Frequency
CREATE OR REPLACE VIEW vw_keyword_frequency AS
SELECT
    k.keyword,
    COUNT(*)       AS report_count,
    SUM(k.frequency) AS total_occurrences,
    c.cohort_name
FROM keywords k
JOIN reports  r ON r.report_id  = k.report_id
JOIN trainees t ON t.trainee_id = r.trainee_id
JOIN cohorts  c ON c.cohort_id  = t.cohort_id
GROUP BY k.keyword, c.cohort_name
ORDER BY total_occurrences DESC;