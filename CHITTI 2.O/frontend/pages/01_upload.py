import streamlit as st
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api_client import client, APIError
from components.sidebar import render_sidebar

st.set_page_config(page_title="Upload — Explain My Data", page_icon="📁", layout="wide")
render_sidebar()

st.title("📁 Upload Dataset")
st.markdown("Upload a CSV or Excel file (max 50 MB) to begin analysis.")

uploaded = st.file_uploader(
    "Choose a file",
    type=["csv", "xlsx", "xls"],
    help="Supported formats: CSV, Excel (.xlsx, .xls)",
)

if uploaded is not None:
    if st.button("Upload & Analyze", type="primary"):
        with st.spinner("Uploading and parsing your file..."):
            try:
                result = client.upload_file(uploaded.getvalue(), uploaded.name)
                st.session_state.session_id = result["session_id"]
                st.session_state.filename = result["filename"]
                st.session_state.rows = result["rows"]
                st.session_state.columns = result["columns"]
                st.session_state.column_names = result["column_names"]
                st.session_state.dtypes = result["dtypes"]
                # Reset conversation history on new upload
                st.session_state.messages = []

                st.success(f"Successfully uploaded **{result['filename']}**")
                col1, col2, col3 = st.columns(3)
                col1.metric("Rows", f"{result['rows']:,}")
                col2.metric("Columns", result["columns"])
                col3.metric("File Size", f"{result['file_size_bytes'] / 1024:.1f} KB")

                st.markdown("### Columns detected")
                dtype_df_data = [
                    {"Column": col, "Type": dtype}
                    for col, dtype in result["dtypes"].items()
                ]
                st.dataframe(dtype_df_data, use_container_width=True)

                st.info("Use the sidebar to navigate to Profile, Visualize, Insights, or Predict.")
            except APIError as e:
                st.error(f"Upload failed: {e}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
