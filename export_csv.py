import pandas as pd
from sqlalchemy import create_engine, text
import config

engine = create_engine(config.DB_URL)

with engine.connect() as conn:
    pd.read_sql(text('SELECT * FROM vw_trainee_scores'), conn).to_csv(config.DATA_DIR / 'trainee_scores.csv', index=False)
    pd.read_sql(text('SELECT * FROM vw_cohort_summary'), conn).to_csv(config.DATA_DIR / 'cohort_summary.csv', index=False)
    pd.read_sql(text('SELECT * FROM vw_at_risk'), conn).to_csv(config.DATA_DIR / 'at_risk.csv', index=False)

    skill_gaps = pd.read_sql(text('SELECT * FROM vw_skill_gaps'), conn)
    skill_gaps.columns = ['Cohort', 'Technical', 'Clarity', 'Methodology', 'Results', 'References']
    skill_gaps.to_csv(config.DATA_DIR / 'skill_gaps.csv', index=False)

    pd.read_sql(text('SELECT * FROM vw_keyword_frequency'), conn).to_csv(config.DATA_DIR / 'keywords.csv', index=False)

print('All CSVs exported')
