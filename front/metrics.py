import os
import json
import base64
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# 1) STREAMLIT PAGE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Shakers AI Metrics Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# 2) INJECT CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
      html, body, .stApp {
        background: linear-gradient(180deg, #0a2b10 0%, #14421f 80%) !important;
        color: #e6f0e8 !important;
      }
      .metric-bubble {
        background: rgba(200, 200, 200, 0.2);
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
      }
      .metric-title { font-size: 1rem !important; color: #b2ccb6 !important; margin: 0; }
      .metric-value { font-size: 2.5rem !important; color: #ffffff !important; margin: 4px 0 0 0; }
      .divider { border:none; border-top:1px solid #2f5b3f; margin:24px 0; }
      footer { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# 3) HEADER WITH LOGO AND TITLE
# ─────────────────────────────────────────────────────────────────────────────
script_dir = os.path.dirname(__file__)
logo_path = os.path.join(script_dir, "logo.png")
with open(logo_path, "rb") as f:
    logo_b64 = base64.b64encode(f.read()).decode()

st.markdown(
    f"""
    <div style="display:flex; align-items:center; padding:20px 0;">
      <img src="data:image/png;base64,{logo_b64}" style="width:50px; height:50px;"/>
      <h1 style="margin-left:16px; color:#c3dc62;">Shakers AI Metrics Dashboard</h1>
    </div>
    <hr class="divider"/>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# 4) LOAD METRICS JSON
# ─────────────────────────────────────────────────────────────────────────────
metrics_path = os.path.join(os.getcwd(), "evaluation", "metrics_summary.json")
if not os.path.exists(metrics_path):
    st.error("Metrics summary not found. Run evaluation/evaluate.py first.")
    st.stop()

with open(metrics_path, "r", encoding="utf-8") as mf:
    m = json.load(mf)

# ─────────────────────────────────────────────────────────────────────────────
# 5) DISPLAY RAG METRICS
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("RAG Evaluation Metrics")
rag = m["rag"]
col1, col2, col3 = st.columns(3, gap="large")
for col, title, value in [
    (col1, "Total Queries", rag["total_queries"]),
    (col2, "Avg Overlap", f"{rag['avg_overlap']*100:.1f}%"),
    (col3, "Avg Recall", f"{rag['avg_recall']*100:.1f}%"),
]:
    with col:
        st.markdown(
            f"""
            <div class="metric-bubble">
              <p class="metric-title">{title}</p>
              <p class="metric-value">{value}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<hr class="divider"/>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# 6) DISPLAY RECOMMENDATION METRICS
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Recommendation Service Metrics")
recs = m["recs"]
col4, col5, col6 = st.columns(3, gap="large")
diversity = (recs["avg_unique"] / recs["avg_recs"] * 100) if recs["avg_recs"] else 0
for col, title, value in [
    (col4, "Total Users", recs["total_users"]),
    (col5, "Avg Recommendations", f"{recs['avg_recs']:.1f}"),
    (col6, "Recommendation Diversity", f"{diversity:.1f}% unique"),
]:
    with col:
        st.markdown(
            f"""
            <div class="metric-bubble">
              <p class="metric-title">{title}</p>
              <p class="metric-value">{value}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown('<hr class="divider"/>', unsafe_allow_html=True)
