import streamlit as st
from src.utils.i18n import get_text

# Mobile-responsive CSS: collapses side-by-side columns to stacked on narrow viewports.
# Streamlit renders columns as divs with data-testid="column".
# At < 640px (typical mobile width), force full width and remove horizontal overflow.
_MOBILE_CSS = """
<style>
/* Collapse multi-column layouts to single column on narrow mobile screens */
@media (max-width: 640px) {
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 100% !important;
    }
    /* Ensure charts don't overflow viewport horizontally */
    .js-plotly-plot, .plotly, .plot-container {
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }
    /* Reduce dataframe horizontal scroll pressure */
    [data-testid="stDataFrame"] {
        font-size: 0.75rem !important;
    }
    /* Reduce metric card font on mobile */
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
}
</style>
"""


def inject_mobile_css():
    """Inject responsive CSS into the Streamlit page. Call once per page."""
    st.markdown(_MOBILE_CSS, unsafe_allow_html=True)


def render_kpi_card(title: str, value: str, delta: str = None, delta_color: str = "normal", help_text: str = None):
    """Render a clean executive KPI metric card with optional help tooltips."""
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )
