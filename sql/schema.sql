-- =============================================================================
-- TPIS · schema.sql
-- =============================================================================

USE tpis;

-- 1. Cohorts
CREATE TABLE IF NOT EXISTS cohorts (
    cohort_id    INT AUTO_INCREMENT PRIMARY KEY,
    cohort_name  VARCHAR(100) NOT NULL,
    start_date   DATE,
    end_date     DATE,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Trainees
CREATE TABLE IF NOT EXISTS trainees (
    trainee_id   INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(150) NOT NULL,
    cohort_id    INT,
    upload_date  DATE,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cohort_id) REFERENCES cohorts(cohort_id)
);

-- 3. Reports
CREATE TABLE IF NOT EXISTS reports (
    report_id    INT AUTO_INCREMENT PRIMARY KEY,
    trainee_id   INT NOT NULL,
    filename     VARCHAR(255),
    upload_date  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status       ENUM('pending','processing','scored','failed') DEFAULT 'pending',
    FOREIGN KEY (trainee_id) REFERENCES trainees(trainee_id)
);

-- 4. Scores
CREATE TABLE IF NOT EXISTS scores (
    score_id         INT AUTO_INCREMENT PRIMARY KEY,
    report_id        INT NOT NULL,
    technical_depth  INT,
    clarity          INT,
    methodology      INT,
    results          INT,
    references_score INT,
    total            INT,
    feedback         TEXT,
    scored_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (report_id) REFERENCES reports(report_id)
);

-- 5. Keywords
CREATE TABLE IF NOT EXISTS keywords (
    keyword_id   INT AUTO_INCREMENT PRIMARY KEY,
    report_id    INT NOT NULL,
    keyword      VARCHAR(100),
    frequency    INT DEFAULT 1,
    FOREIGN KEY (report_id) REFERENCES reports(report_id)
);