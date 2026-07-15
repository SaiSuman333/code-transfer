import plotly.graph_objects as go
import streamlit as st


def render_chart(plotly_json: dict, key: str = "chart") -> None:
    try:
        fig = go.Figure(plotly_json)
        st.plotly_chart(fig, use_container_width=True, key=key)
    except Exception as e:
        st.error(f"Failed to render chart: {e}")
