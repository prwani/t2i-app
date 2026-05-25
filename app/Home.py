"""Streamlit entrypoint with grouped navigation."""

import streamlit as st


st.set_page_config(page_title="T2I App", page_icon="T2I", layout="wide")

navigation = st.navigation(
    {
        "Create": [
            st.Page(
                "views/asset_creation_workflow.py",
                title="Asset Creation Workflow",
                icon="✨",
                default=True,
            ),
        ],
        "Evaluation Utils": [
            st.Page("views/evaluate.py", title="Evaluate", icon="✅"),
            st.Page("views/compare.py", title="Compare", icon="📊"),
            st.Page("views/batch_rank.py", title="Batch Rank", icon="🏆"),
        ],
    }
)

navigation.run()
