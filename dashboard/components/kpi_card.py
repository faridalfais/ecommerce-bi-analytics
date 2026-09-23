import streamlit as st

def render_kpi_card(title: str, value: str, delta: str = None, delta_color: str = "normal", help_text: str = None):
    """Render a clean executive KPI metric card with optional help tooltips."""
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )
