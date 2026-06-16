import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

engine = create_engine('mysql+mysqlconnector://root:KHUSHALnagal%4005%23@localhost:3306/tpis')

with engine.connect() as conn:
    pd.read_sql(text('SELECT * FROM vw_trainee_scores'), conn).to_csv('data/trainee_scores.csv', index=False)
    pd.read_sql(text('SELECT * FROM vw_cohort_summary'), conn).to_csv('data/cohort_summary.csv', index=False)
    pd.read_sql(text('SELECT * FROM vw_at_risk'), conn).to_csv('data/at_risk.csv', index=False)
    
    skill_gaps = pd.read_sql(text('SELECT * FROM vw_skill_gaps'), conn)
    skill_gaps.columns = ['Cohort', 'Technical', 'Clarity', 'Methodology', 'Results', 'References']
    skill_gaps.to_csv('data/skill_gaps.csv', index=False)
    
    pd.read_sql(text('SELECT * FROM vw_keyword_frequency'), conn).to_csv('data/keywords.csv', index=False)

print('All CSVs exported')