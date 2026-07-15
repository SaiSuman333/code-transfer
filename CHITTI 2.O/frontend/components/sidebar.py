import streamlit as st


SIDEBAR_STYLE = """
<style>
/* ── Hide Streamlit's auto-generated page navigation ── */
[data-testid="stSidebarNav"] { display: none !important; }

/* ── Remove default top padding in sidebar ── */
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}
section[data-testid="stSidebar"] > div {
    padding-top: 0 !important;
}

/* ── Sidebar background ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 60%, #16213e 100%) !important;
    border-right: 1px solid #2a2a4a !important;
}

/* ── Logo block ── */
.sb-logo {
    text-align: center;
    padding: 1.4rem 0.5rem 0.6rem 0.5rem;
}
.sb-icon {
    font-size: 2.4rem;
    display: block;
    margin-bottom: 0.3rem;
    filter: drop-shadow(0 0 10px #7c6af7);
}
.sb-title {
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    color: #e2e0ff;
    line-height: 1.3;
}
.sb-subtitle {
    font-size: 0.68rem;
    color: #6666aa;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-top: 0.2rem;
}

/* ── Divider ── */
.sb-divider {
    border: none;
    border-top: 1px solid #2a2a4a;
    margin: 0.6rem 0;
}

/* ── Dataset info card ── */
.sb-card {
    background: rgba(124, 106, 247, 0.07);
    border: 1px solid rgba(124, 106, 247, 0.22);
    border-radius: 10px;
    padding: 0.65rem 0.9rem;
    margin: 0 0 0.7rem 0;
}
.sb-card-title {
    font-size: 0.62rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #7c6af7;
    font-weight: 700;
    margin-bottom: 0.45rem;
}
.sb-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.2rem;
}
.sb-label {
    font-size: 0.75rem;
    color: #7777aa;
}
.sb-value {
    font-size: 0.8rem;
    font-weight: 600;
    color: #e2e0ff;
    max-width: 58%;
    text-align: right;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* ── Nav section label ── */
.sb-nav-label {
    font-size: 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    color: #444466;
    font-weight: 700;
    padding: 0 0.1rem;
    margin-bottom: 0.25rem;
}

/* ── Page link styling ── */
[data-testid="stSidebar"] [data-testid="stPageLink"] a,
[data-testid="stSidebar"] [data-testid="stPageLink"] a p {
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: #a0a0cc !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"] {
    border-radius: 8px;
    margin-bottom: 0.1rem;
}
[data-testid="stSidebar"] [data-testid="stPageLink"]:hover a,
[data-testid="stSidebar"] [data-testid="stPageLink"]:hover a p {
    color: #e2e0ff !important;
}
[data-testid="stSidebar"] [data-testid="stPageLink"]:hover {
    background: rgba(124, 106, 247, 0.15);
}

/* ── No-dataset state ── */
.sb-empty {
    text-align: center;
    padding: 0.8rem 0.4rem;
}
.sb-empty-icon { font-size: 1.8rem; display: block; margin-bottom: 0.4rem; opacity: 0.45; }
.sb-empty p   { font-size: 0.78rem; color: #555577; margin-bottom: 0.6rem; line-height: 1.5; }

/* ── Footer ── */
.sb-footer {
    text-align: center;
    padding: 0.6rem 0;
    font-size: 0.62rem;
    color: #333355;
    letter-spacing: 0.06em;
    border-top: 1px solid #1e1e3a;
    margin-top: 1rem;
}
</style>
"""


def render_sidebar():
    with st.sidebar:
        st.markdown(SIDEBAR_STYLE, unsafe_allow_html=True)

        # ── Logo ──
        st.markdown("""
        <div class="sb-logo">
            <span class="sb-icon">📊</span>
            <div class="sb-title">Explain My Data</div>
            <div class="sb-subtitle">AI-Free Analysis Platform</div>
        </div>
        <hr class="sb-divider">
        """, unsafe_allow_html=True)

        if st.session_state.get("session_id"):
            filename = st.session_state.get("filename", "—")
            rows     = st.session_state.get("rows", 0)
            cols     = st.session_state.get("columns", 0)

            # ── Dataset card ──
            st.markdown(f"""
            <div class="sb-card">
                <div class="sb-card-title">Active Dataset</div>
                <div class="sb-row">
                    <span class="sb-label">File</span>
                    <span class="sb-value" title="{filename}">{filename}</span>
                </div>
                <div class="sb-row">
                    <span class="sb-label">Rows</span>
                    <span class="sb-value">{rows:,}</span>
                </div>
                <div class="sb-row">
                    <span class="sb-label">Columns</span>
                    <span class="sb-value">{cols}</span>
                </div>
            </div>
            <div class="sb-nav-label">Pages</div>
            """, unsafe_allow_html=True)

            st.page_link("pages/01_upload.py",    label="Upload",    icon="📁")
            st.page_link("pages/02_profile.py",   label="Profile",   icon="🔍")
            st.page_link("pages/03_visualize.py", label="Visualize", icon="📈")
            st.page_link("pages/04_insights.py",  label="Insights",  icon="💡")
            st.page_link("pages/05_predict.py",   label="Predict",   icon="🔮")

        else:
            st.markdown("""
            <div class="sb-empty">
                <span class="sb-empty-icon">📂</span>
                <p>No dataset loaded.<br>Upload a file to get started.</p>
            </div>
            """, unsafe_allow_html=True)
            st.page_link("pages/01_upload.py", label="Upload a file to begin", icon="📁")

        st.markdown('<div class="sb-footer">Explain My Data · v2.0</div>', unsafe_allow_html=True)
