import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api_client import client, APIError
from components.sidebar import render_sidebar

st.set_page_config(page_title="Insights — Explain My Data", page_icon="💡", layout="wide")
render_sidebar()

st.title("💡 Insights")
st.markdown(
    "Automatically detected statistical patterns, anomalies, and data quality issues. "
    "Each insight is computed directly from your data — no AI API required."
)

if not st.session_state.get("session_id"):
    st.warning("Please upload a dataset first.")
    st.stop()

SEVERITY_COLOR = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
CATEGORY_ICON = {
    "correlation": "🔗",
    "outlier": "📍",
    "skewness": "📐",
    "missing_data": "❓",
    "distribution": "📊",
    "duplicate": "♊",
}
CATEGORY_DESCRIPTION = {
    "correlation": "Two columns that change together (positively or negatively).",
    "outlier": "Values that fall unusually far from the typical range.",
    "skewness": "The distribution is not symmetric — one tail is longer than the other.",
    "missing_data": "The column has a significant number of blank / null values.",
    "distribution": "The shape or spread of values is unusual.",
    "duplicate": "Identical rows appear more than once in the dataset.",
}

with st.spinner("Analysing dataset for insights..."):
    try:
        data = client.get_insights(st.session_state.session_id)
    except APIError as e:
        st.error(f"Failed to load insights: {e}")
        st.stop()

insights = data["insights"]

if not insights:
    st.success("No significant issues found in your dataset. The data looks clean!")
    st.stop()

# Summary bar
critical = sum(1 for i in insights if i["severity"] == "critical")
warnings = sum(1 for i in insights if i["severity"] == "warning")
info = sum(1 for i in insights if i["severity"] == "info")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Insights", data["total"])
c2.metric("🔴 Critical", critical)
c3.metric("🟡 Warning", warnings)
c4.metric("🔵 Info", info)

st.markdown("---")

# Group by severity
for severity in ["critical", "warning", "info"]:
    group = [i for i in insights if i["severity"] == severity]
    if not group:
        continue
    st.subheader(f"{SEVERITY_COLOR[severity]} {severity.capitalize()} ({len(group)})")
    for insight in group:
        icon = CATEGORY_ICON.get(insight["category"], "📌")
        cat_desc = CATEGORY_DESCRIPTION.get(insight["category"], "")
        with st.expander(f"{icon} {insight['title']}"):
            st.markdown(insight["description"])
            if cat_desc:
                st.caption(f"**Category:** {insight['category'].replace('_', ' ').title()} — {cat_desc}")
            if insight.get("affected_columns"):
                st.markdown(f"**Affected columns:** `{'`, `'.join(insight['affected_columns'])}`")
            if insight.get("metric_value") is not None:
                st.markdown(f"**Metric value:** `{insight['metric_value']}`")

st.markdown("---")

# Auto-generated summary — no LLM needed
st.subheader("📋 Auto-Generated Summary")
detail_level = st.radio("Detail level", ["brief", "detailed"], horizontal=True)

with st.spinner("Generating summary..."):
    try:
        result = client.explain_insights(
            st.session_state.session_id,
            {"detail_level": detail_level},
        )
        st.markdown(result["explanation"])
        st.caption("Generated using statistical templates — no AI API required.")
    except APIError as e:
        st.error(f"Summary generation failed: {e}")
