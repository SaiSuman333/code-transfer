import streamlit as st
import sys, os
import plotly.graph_objects as go

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api_client import client, APIError
from components.sidebar import render_sidebar
from components.chart_renderer import render_chart

st.set_page_config(page_title="Predict — Explain My Data", page_icon="🔮", layout="wide")
render_sidebar()

st.title("🔮 Predictive Analytics")
st.markdown(
    "Train a **Random Forest** model to predict a target column from your data. "
    "Results include performance metrics, a visual, feature importances, and a plain-English model report."
)

if not st.session_state.get("session_id"):
    st.warning("Please upload a dataset first.")
    st.stop()

cols = st.session_state.column_names
dtypes = st.session_state.dtypes

target_col = st.selectbox("Target Column (what to predict)", cols)
feature_cols = st.multiselect(
    "Feature Columns (leave empty to auto-select)",
    [c for c in cols if c != target_col],
    default=[],
)
task_type = st.selectbox("Task Type", ["auto", "regression", "classification"])
test_size = st.slider("Test Set Size", 0.1, 0.4, 0.2, 0.05)

if st.button("Run Prediction", type="primary"):
    payload = {
        "target_column": target_col,
        "feature_columns": feature_cols if feature_cols else None,
        "task_type": task_type,
        "test_size": test_size,
    }
    with st.spinner("Training model and generating insights... this may take a moment."):
        try:
            result = client.predict(st.session_state.session_id, payload)

            st.success(f"Model trained: **{result['model_name']}** ({result['task_type']})")

            # Metrics
            st.subheader("Model Performance")
            metric_cols = st.columns(len(result["metrics"]))
            for i, (k, v) in enumerate(result["metrics"].items()):
                metric_cols[i].metric(k.upper().replace("_", " "), f"{v:.4f}")

            # Chart
            if result.get("plotly_json"):
                st.subheader("Model Results")
                render_chart(result["plotly_json"], key="predict_chart")

            # Feature importance
            st.subheader("Feature Importances")
            fi_data = result["feature_importances"][:15]
            if fi_data:
                import plotly.express as px
                fig = px.bar(
                    fi_data,
                    x="importance", y="feature",
                    orientation="h",
                    title="Top Feature Importances",
                    labels={"importance": "Importance", "feature": "Feature"},
                )
                fig.update_layout(template="plotly_white", yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(fig, use_container_width=True)

            # Model Report (template-based, no LLM)
            st.subheader("📋 Model Report")
            st.markdown(result["explanation"])
            st.caption("Generated using statistical templates — no AI API required.")

        except APIError as e:
            st.error(f"Prediction failed: {e}")
