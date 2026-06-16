# =============================================================================
# TPIS · dashboard/overview.py
# Main Streamlit dashboard
# =============================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    f"mysql+mysqlconnector://{config.DB_USER}:{quote_plus(config.DB_PASSWORD)}"
    f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}",
    pool_pre_ping=True
)

def load(query):
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TPIS Dashboard",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 TPIS · Trainee Performance Intelligence System")
st.markdown("---")

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.header("Filters")
cohorts = load("SELECT DISTINCT cohort_name FROM cohorts")
cohort_list = ["All"] + cohorts["cohort_name"].tolist()
selected_cohort = st.sidebar.selectbox("Select Cohort", cohort_list)

# ── Load Data ─────────────────────────────────────────────────────────────────
scores_df = load("SELECT * FROM vw_trainee_scores")
summary_df = load("SELECT * FROM vw_cohort_summary")
at_risk_df = load("SELECT * FROM vw_at_risk")
gaps_df    = load("SELECT * FROM vw_skill_gaps")

if selected_cohort != "All":
    scores_df  = scores_df[scores_df["cohort_name"] == selected_cohort]
    at_risk_df = at_risk_df[at_risk_df["cohort_name"] == selected_cohort]

# ── KPI Cards ─────────────────────────────────────────────────────────────────
st.subheader("📊 Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Trainees",  len(scores_df))
c2.metric("Average Score",   f"{scores_df['total'].mean():.1f}" if not scores_df.empty else "—")
c3.metric("Top Score",       scores_df['total'].max() if not scores_df.empty else "—")
c4.metric("At Risk",         len(at_risk_df))

st.markdown("---")

# ── Score Distribution ────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Score Distribution")
    if not scores_df.empty:
        fig = px.histogram(
            scores_df, x="total", nbins=10,
            color_discrete_sequence=["#4F8EF7"],
            labels={"total": "Total Score"}
        )
        fig.update_layout(showlegend=False, height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet.")

with col2:
    st.subheader("🕸️ Skill Radar")
    if not gaps_df.empty:
        row = gaps_df.iloc[0]
        categories = ["Technical Depth","Clarity","Methodology","Results","References"]
        values = [
            row["avg_technical_depth"], row["avg_clarity"],
            row["avg_methodology"],     row["avg_results"],
            row["avg_references"]
        ]
        fig = go.Figure(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            line_color="#4F8EF7"
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,100])),
            height=300, showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data yet.")

st.markdown("---")

# ── Trainee Table ─────────────────────────────────────────────────────────────
st.subheader("📋 Trainee Scores")
if not scores_df.empty:
    st.dataframe(
        scores_df[[
            "trainee_name","cohort_name","technical_depth",
            "clarity","methodology","results","references_score","total"
        ]].sort_values("total", ascending=False),
        use_container_width=True
    )
else:
    st.info("No scores yet.")

st.markdown("---")

# ── At Risk ───────────────────────────────────────────────────────────────────
st.subheader("⚠️ At-Risk Trainees")
if not at_risk_df.empty:
    st.dataframe(at_risk_df, use_container_width=True)
else:
    st.success("✅ No at-risk trainees in selected cohort.")