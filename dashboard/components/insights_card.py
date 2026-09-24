import streamlit as st
from src.utils.i18n import get_text


def render_insights_card(insights_dict: dict, lang: str = "en"):
    """Render executive decision narrative card with structured sections.

    On wide screens: 2-column layout (What Happened / Why | Impact / Watch).
    On mobile: collapses to single column via responsive CSS in kpi_card.inject_mobile_css().
    """
    st.markdown("---")
    st.subheader(get_text('section_executive_insights', lang))

    ins = insights_dict.get(lang, insights_dict.get("en", {}))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### 1. {get_text('what_happened', lang)}")
        st.info(ins.get("what_happened", ""))

        st.markdown(f"#### 2. {get_text('why', lang)}")
        st.info(ins.get("why", ""))

    with col2:
        st.markdown(f"#### 3. {get_text('business_impact', lang)}")
        st.warning(ins.get("business_impact", ""))

        st.markdown(f"#### 4. {get_text('what_should_management_watch', lang)}")
        st.success(ins.get("what_should_management_watch", ""))
