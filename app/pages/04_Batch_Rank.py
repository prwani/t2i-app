"""Generate and rank image variations."""

import streamlit as st

from app.components.image_gallery import render_gallery
from app.services import generate_and_rank, run_async


st.title("Batch Rank")
st.write("Generate GPT-Image-2 variations and rank them with the selected evaluation layers.")

prompt = st.text_area("Prompt", height=120)
count = st.slider("Variations", 2, 10, 3)
quality = st.selectbox("Quality", ["low", "medium", "high"], index=0)
layers = st.multiselect("Layers", ["embedding", "rubric", "judge"], default=["embedding", "rubric", "judge"])

if st.button("Generate and rank", type="primary", disabled=not prompt.strip() or not layers):
    with st.status("Generating and evaluating variations...", expanded=True):
        assets = run_async(
            generate_and_rank(
                prompt,
                n=count,
                quality=quality,
                layers=layers,  # type: ignore[arg-type]
            )
        )
        st.session_state["ranked_assets"] = assets
        st.write("Ranking complete.")

render_gallery(st.session_state.get("ranked_assets", []))
