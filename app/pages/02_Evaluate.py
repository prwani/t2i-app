"""Image evaluation page."""

import streamlit as st

from components.evaluation_report import render_evaluation_report
from services import evaluate_image, run_async


st.title("Evaluate")

uploaded = st.file_uploader("Image", type=["png", "jpg", "jpeg", "webp"])
prompt = st.text_area("Prompt", height=120)
layers = st.multiselect(
    "Evaluation layers",
    ["embedding", "rubric", "judge"],
    default=["embedding", "rubric", "judge"],
)

if uploaded and prompt.strip():
    st.image(uploaded.getvalue(), caption=uploaded.name, width=360)

if st.button("Evaluate", type="primary", disabled=uploaded is None or not prompt.strip() or not layers):
    with st.status("Evaluating image...", expanded=True):
        try:
            report = run_async(
                evaluate_image(
                    uploaded.getvalue(),
                    prompt,
                    layers,  # type: ignore[arg-type]
                    image_path=uploaded.name,
                )
            )
            st.session_state["evaluation_report"] = report
            st.write("Evaluation complete.")
        except Exception as exc:
            st.error(f"Evaluation failed: {exc}")

if "evaluation_report" in st.session_state:
    render_evaluation_report(st.session_state["evaluation_report"])
