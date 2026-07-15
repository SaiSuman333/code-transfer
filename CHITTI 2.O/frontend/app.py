import streamlit as st

st.set_page_config(
    page_title="Explain My Data",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "filename" not in st.session_state:
    st.session_state.filename = None
if "column_names" not in st.session_state:
    st.session_state.column_names = []
if "dtypes" not in st.session_state:
    st.session_state.dtypes = {}
if "rows" not in st.session_state:
    st.session_state.rows = 0
if "columns" not in st.session_state:
    st.session_state.columns = 0

st.title("📊 Explain My Data")
st.markdown("An AI-powered data analysis platform. Upload a CSV or Excel file to get started.")

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.info("**Step 1:** Upload your dataset")
with col2:
    st.info("**Step 2:** Explore profile, charts & insights")
with col3:
    st.info("**Step 3:** Chat with AI or run predictions")

st.markdown("---")
st.markdown("Use the **sidebar** to navigate between pages.")
