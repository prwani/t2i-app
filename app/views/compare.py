"""Compare uploaded images."""

import streamlit as st

from components.evaluation_report import render_evaluation_report, render_evaluation_summary
from services import evaluate_image, run_async


st.title("Compare")

uploads = st.file_uploader(
    "Images to compare",
    type=["png", "jpg", "jpeg", "webp"],
    accept_multiple_files=True,
)
prompt = st.text_area("Shared prompt", height=120)
layers = st.multiselect("Layers", ["embedding", "rubric", "judge"], default=["embedding", "rubric", "judge"])

if st.button("Evaluate comparison", type="primary", disabled=not uploads or not prompt.strip() or not layers):
    reports = []
    with st.status("Evaluating images...", expanded=True):
        for upload in uploads:
            st.write(f"Evaluating {upload.name}")
            try:
                reports.append(
                    run_async(
                        evaluate_image(
                            upload.getvalue(),
                            prompt,
                            layers,  # type: ignore[arg-type]
                            image_path=upload.name,
                        )
                    )
                )
            except Exception as exc:
                st.error(f"Evaluation failed for {upload.name}: {exc}")
    st.session_state["compare_reports"] = reports

reports = st.session_state.get("compare_reports", [])
if reports:
    render_evaluation_summary(reports)

for report in reports:
    st.subheader(report.image_path or "Image")
    render_evaluation_report(report)
