import streamlit as st
import sys, os
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api_client import client, APIError
from components.sidebar import render_sidebar

st.set_page_config(page_title="Profile — Explain My Data", page_icon="🔍", layout="wide")
render_sidebar()

st.title("🔍 Data Profile")

if not st.session_state.get("session_id"):
    st.warning("Please upload a dataset first.")
    st.stop()

with st.spinner("Profiling dataset..."):
    try:
        profile = client.get_profile(st.session_state.session_id)
    except APIError as e:
        st.error(f"Failed to load profile: {e}")
        st.stop()

# Overview metrics
st.subheader("Dataset Overview")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Rows", f"{profile['rows']:,}")
c2.metric("Columns", profile["total_columns"])
c3.metric("Numeric", len(profile["numeric_columns"]))
c4.metric("Categorical", len(profile["categorical_columns"]))
c5.metric("Duplicate Rows", profile["duplicate_rows"])

st.markdown(f"**Memory Usage:** {profile['memory_usage_mb']} MB")
st.markdown("---")

# Missing values summary
st.subheader("Missing Values")
missing_data = [
    {"Column": c["name"], "Missing %": c["null_percentage"], "Missing Count": c["null_count"]}
    for c in profile["columns"] if c["null_count"] > 0
]
if missing_data:
    fig = px.bar(
        missing_data, x="Column", y="Missing %",
        title="Columns with Missing Values (%)",
        color="Missing %", color_continuous_scale="Reds",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.success("No missing values found!")

st.markdown("---")

# Column details
st.subheader("Column Details")
tab_num, tab_cat = st.tabs(["Numeric Columns", "Categorical Columns"])

with tab_num:
    num_cols = [c for c in profile["columns"] if c["name"] in profile["numeric_columns"]]
    if num_cols:
        rows = []
        for c in num_cols:
            rows.append({
                "Column": c["name"],
                "Type": c["dtype"],
                "Non-null": c["non_null_count"],
                "Null %": c["null_percentage"],
                "Unique": c["unique_count"],
                "Mean": round(c["mean"], 4) if c["mean"] is not None else None,
                "Median": round(c["median"], 4) if c["median"] is not None else None,
                "Std": round(c["std"], 4) if c["std"] is not None else None,
                "Min": c["min"],
                "Max": c["max"],
                "Skewness": round(c["skewness"], 4) if c["skewness"] is not None else None,
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No numeric columns found.")

with tab_cat:
    cat_cols = [c for c in profile["columns"] if c["name"] in profile["categorical_columns"]]
    if cat_cols:
        selected = st.selectbox("Select a column to inspect", [c["name"] for c in cat_cols])
        col_data = next(c for c in cat_cols if c["name"] == selected)
        st.markdown(f"**Unique values:** {col_data['unique_count']} | **Null %:** {col_data['null_percentage']}%")
        if col_data.get("top_values"):
            fig = px.bar(
                col_data["top_values"], x="value", y="count",
                title=f"Top Values — {selected}",
                labels={"value": selected, "count": "Count"},
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No categorical columns found.")
