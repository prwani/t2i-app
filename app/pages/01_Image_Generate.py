"""Image generation page."""

import streamlit as st

from components.image_gallery import render_gallery
from services import generate_aspect_package, generate_images, run_async


st.title("Image Generate")

with st.sidebar:
    model = st.selectbox("Model", ["gpt-image-2", "MAI-Image-2", "MAI-Image-2e"])
    scenario = st.selectbox("Scenario", ["text", "aspect-ratio package"])
    quality = st.selectbox("Quality", ["low", "medium", "high"], index=2)
    size = st.selectbox("Size", ["1024x1024", "1536x1024", "1024x1536"])
    count = st.slider("Images", 1, 4, 1)

prompt = st.text_area("Prompt", height=120)
formats = st.multiselect(
    "Target formats",
    ["instagram_square", "instagram_story", "linkedin_banner", "desktop_hero", "mobile_story"],
    default=["instagram_square", "linkedin_banner"],
    disabled=scenario != "aspect-ratio package",
)

if st.button("Generate", type="primary", disabled=not prompt.strip()):
    with st.status("Generating images...", expanded=True):
        if scenario == "aspect-ratio package":
            assets = run_async(generate_aspect_package(prompt, model, formats, quality=quality))
        else:
            assets = run_async(generate_images(prompt, model, size=size, quality=quality, n=count))
        st.session_state["generated_assets"] = assets
        st.write("Generation complete.")

render_gallery(st.session_state.get("generated_assets", []))
