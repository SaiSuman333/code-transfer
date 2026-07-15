import streamlit as st
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from api_client import client, APIError
from components.sidebar import render_sidebar
from components.chart_renderer import render_chart

st.set_page_config(page_title="Visualize — Explain My Data", page_icon="📈", layout="wide")
render_sidebar()

st.title("📈 Visualize")
st.markdown("Explore your dataset visually. Build custom charts or use Quick Charts for instant insights.")

if not st.session_state.get("session_id"):
    st.warning("Please upload a dataset first.")
    st.stop()

cols      = st.session_state.column_names
dtypes    = st.session_state.dtypes
all_cols  = cols
numeric_cols = [c for c, d in dtypes.items() if any(t in d for t in ["int", "float"])]
cat_cols     = [c for c in cols if c not in numeric_cols]

# ── Chart type registry ────────────────────────────────────────────────────

CHART_TYPES = {
    "Histogram":               "histogram",
    "KDE Distribution":        "kde",
    "Box Plot":                "box",
    "Violin Plot":             "violin",
    "Bar Chart":               "bar",
    "Horizontal Bar Chart":    "bar_horizontal",
    "Pie Chart":               "pie",
    "Donut Chart":             "donut",
    "Scatter Plot":            "scatter",
    "Line Chart":              "line",
    "Area Chart":              "area",
    "Scatter Matrix":          "scatter_matrix",
    "Correlation Heatmap":     "correlation_heatmap",
}

CHART_DESCRIPTIONS = {
    "histogram":          "Shows how many values fall into each range. Good for spotting where most values cluster.",
    "kde":                "A smooth curve showing the shape of a numeric column's distribution.",
    "box":                "Shows median, spread, and outliers. Great for comparing groups.",
    "violin":             "Like a box plot but also shows the full distribution shape.",
    "bar":                "Counts or averages per category — classic comparison chart.",
    "bar_horizontal":     "Same as bar but flipped. Best when category names are long (e.g. countries, products).",
    "pie":                "Proportions as slices. Best with fewer than 8 categories.",
    "donut":              "Pie chart with a hole — slightly easier to read proportions.",
    "scatter":            "Two numeric columns plotted against each other. Great for spotting relationships.",
    "line":               "Connects points in order. Use only when X has a natural sequence (e.g. time).",
    "area":               "Like a line chart but filled below — emphasises volume over time.",
    "scatter_matrix":     "Every numeric column vs every other — a full overview of relationships at once.",
    "correlation_heatmap":"Colour-coded grid showing how strongly each pair of columns is related.",
}


def _suggest_chart(x: str | None, y: str | None) -> tuple[str, str]:
    """Return (chart_type_key, reason) based on selected columns."""
    x_num = x in numeric_cols if x else False
    y_num = y in numeric_cols if y else True   # no y selected → treat as numeric intent

    if x and y:
        if x_num and y_num:
            return "Scatter Plot", "Two numeric columns → Scatter Plot is best for spotting relationships."
        if not x_num and y_num:
            return "Horizontal Bar Chart", "Category + numeric → Horizontal Bar Chart for easy comparison."
        if x_num and not y_num:
            return "Box Plot", "Numeric + category → Box Plot to compare distributions per group."
    if x and not y:
        if x_num:
            return "Histogram", "Single numeric column → Histogram shows how values are distributed."
        else:
            return "Horizontal Bar Chart", "Single category column → Bar Chart to count each value."
    if not x and not y:
        if len(numeric_cols) >= 2:
            return "Correlation Heatmap", "Multiple numeric columns → Heatmap shows all relationships at once."
    return "Histogram", ""


def _render_chart_safe(payload: dict, key: str, height: int):
    try:
        result = client.create_chart(st.session_state.session_id, payload)
        fig_json = result["plotly_json"]
        fig_json.setdefault("layout", {})["height"] = height
        render_chart(fig_json, key=key)
    except APIError as e:
        st.warning(f"Could not generate chart: {e}")


# ══════════════════════════════════════════════════════════════════════════
# TABS: Quick Charts | Custom Chart
# ══════════════════════════════════════════════════════════════════════════

tab_quick, tab_custom = st.tabs(["⚡ Quick Charts", "🛠️ Custom Chart"])

# ── Quick Charts ──────────────────────────────────────────────────────────
with tab_quick:
    st.markdown(
        "Auto-generated charts based on your data. "
        "These cover the most useful views without any configuration."
    )

    height = st.slider("Chart height (px)", 300, 800, 420, 20, key="qc_height")

    if not numeric_cols and not cat_cols:
        st.info("No columns available for quick charts.")
    else:
        generated = 0

        # Correlation heatmap if 2+ numeric cols
        if len(numeric_cols) >= 2:
            st.subheader("Relationships Between Numeric Columns")
            st.caption("The darker the colour, the stronger the relationship.")
            _render_chart_safe(
                {"chart_type": "correlation_heatmap", "x_column": None, "y_column": None,
                 "color_column": None, "title": "Correlation Heatmap"},
                key="qc_heatmap", height=height,
            )
            generated += 1

        # Distribution of first 4 numeric cols
        if numeric_cols:
            st.subheader("How Numeric Columns Are Distributed")
            st.caption("Each chart shows where values cluster and how spread out they are.")
            grid_cols = st.columns(min(2, len(numeric_cols[:4])))
            for i, col in enumerate(numeric_cols[:4]):
                with grid_cols[i % 2]:
                    _render_chart_safe(
                        {"chart_type": "histogram", "x_column": col, "y_column": None,
                         "color_column": None, "title": f"Distribution of {col}"},
                        key=f"qc_hist_{col}", height=height,
                    )
            generated += 1

        # Top categories for first 2 categorical cols
        if cat_cols:
            st.subheader("Category Breakdown")
            st.caption("Top values in each categorical column.")
            grid_cols = st.columns(min(2, len(cat_cols[:2])))
            for i, col in enumerate(cat_cols[:2]):
                with grid_cols[i % 2]:
                    _render_chart_safe(
                        {"chart_type": "bar_horizontal", "x_column": col, "y_column": None,
                         "color_column": None, "title": f"Top Values — {col}"},
                        key=f"qc_bar_{col}", height=height,
                    )
            generated += 1

        # Scatter of first two numeric cols if they exist
        if len(numeric_cols) >= 2:
            st.subheader(f"Relationship: {numeric_cols[0]} vs {numeric_cols[1]}")
            st.caption("Each dot is one row. A pattern here suggests the columns are related.")
            color_hint = cat_cols[0] if cat_cols else None
            _render_chart_safe(
                {"chart_type": "scatter",
                 "x_column": numeric_cols[0], "y_column": numeric_cols[1],
                 "color_column": color_hint,
                 "title": f"{numeric_cols[0]} vs {numeric_cols[1]}"},
                key="qc_scatter", height=height,
            )

# ── Custom Chart ──────────────────────────────────────────────────────────
with tab_custom:
    st.markdown("Build your own chart by choosing columns and chart type.")

    # Column selectors first — so we can auto-suggest
    cc1, cc2, cc3 = st.columns(3)
    with cc1:
        x_col = st.selectbox("X Column", ["None"] + all_cols, key="cx")
        x_col = None if x_col == "None" else x_col
    with cc2:
        y_col = st.selectbox("Y Column (optional)", ["None"] + all_cols, key="cy")
        y_col = None if y_col == "None" else y_col
    with cc3:
        color_col = st.selectbox("Color by (optional)", ["None"] + all_cols, key="cc")
        color_col = None if color_col == "None" else color_col

    # Auto-suggest
    suggested_label, suggestion_reason = _suggest_chart(x_col, y_col)
    if suggestion_reason:
        st.info(f"💡 **Suggestion:** {suggestion_reason}")

    chart_label = st.selectbox(
        "Chart Type",
        list(CHART_TYPES.keys()),
        index=list(CHART_TYPES.keys()).index(suggested_label),
        key="chart_type_select",
    )
    chart_type = CHART_TYPES[chart_label]
    st.caption(f"**What is this?** {CHART_DESCRIPTIONS[chart_type]}")

    title  = st.text_input("Chart Title (optional)", "", key="ctitle")
    height = st.slider("Chart height (px)", 300, 800, 450, 20, key="cheight")

    if st.button("Generate Chart", type="primary"):
        payload = {
            "chart_type": chart_type,
            "x_column":    x_col,
            "y_column":    y_col,
            "color_column":color_col,
            "title":       title or None,
        }
        with st.spinner("Generating chart..."):
            try:
                result = client.create_chart(st.session_state.session_id, payload)
                fig_json = result["plotly_json"]
                fig_json.setdefault("layout", {})["height"] = height
                render_chart(fig_json, key="custom_chart")
            except APIError as e:
                st.error(f"Chart error: {e}")
